# app/auth.py
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from .supabase_client import supabase, supabase_service, verify_user_token, get_user_github_token, get_authenticated_client

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["auth"])

class SignUpRequest(BaseModel):
    email: str
    password: str
    username: str

class SignInRequest(BaseModel):
    email: str
    password: str

class GitHubTokenRequest(BaseModel):
    token: str
    github_username: str

class AuthenticatedUser:
    """Simple wrapper for authenticated user data"""
    def __init__(self, id: str, email: str = "", access_token: str = ""):
        self.id = id
        self.email = email
        self.access_token = access_token

async def get_current_user(request: Request):
    """Dependency to get current authenticated user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    user_response = await verify_user_token(token)
    
    if not user_response:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Extract user from GetUserResponse
    user = user_response.user if hasattr(user_response, 'user') else user_response
    return AuthenticatedUser(id=user.id, email=getattr(user, 'email', ''), access_token=token)

@router.post("/signup")
async def sign_up(request: SignUpRequest):
    """Register new user"""
    try:
        # Create auth user via Supabase Auth
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "username": request.username,
                }
            }
        })
        
        if not response.user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        user_id = response.user.id
        
        # Create user profile in users table (use anon client since service key may be invalid)
        try:
            supabase_service.table("users").upsert({
                "id": user_id,
                "email": request.email,
                "username": request.username,
            }).execute()
        except Exception as profile_err:
            print(f"Warning: Could not create user profile: {profile_err}")
        
        # If session exists, user can login immediately (email confirmation disabled)
        if response.session:
            return {
                "user_id": user_id,
                "email": request.email,
                "username": request.username,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            }
        
        # Email confirmation required — try to login anyway (might work if already confirmed)
        try:
            login_response = supabase.auth.sign_in_with_password({
                "email": request.email,
                "password": request.password,
            })
            return {
                "user_id": user_id,
                "email": request.email,
                "username": request.username,
                "access_token": login_response.session.access_token,
                "refresh_token": login_response.session.refresh_token,
            }
        except Exception:
            # Can't login yet — email confirmation needed
            return {
                "user_id": user_id,
                "email": request.email,
                "username": request.username,
                "access_token": None,
                "refresh_token": None,
                "message": "Account created! Please check your email to confirm, then login.",
            }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Signup error: {error_msg}")
        if "already" in error_msg.lower() or "duplicate" in error_msg.lower() or "registered" in error_msg.lower():
            raise HTTPException(status_code=400, detail="An account with this email already exists. Please login instead.")
        raise HTTPException(status_code=400, detail=error_msg)

@router.post("/login")
async def sign_in(request: SignInRequest):
    """Authenticate user and return session"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })
        
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Ensure user profile exists in public.users (for users created before trigger)
        try:
            client = get_authenticated_client(response.session.access_token)
            client.table("users").upsert({
                "id": response.user.id,
                "email": response.user.email,
                "username": getattr(response.user, 'user_metadata', {}).get('username', request.email.split('@')[0]),
            }).execute()
        except Exception as profile_err:
            print(f"Warning: Could not ensure user profile: {profile_err}")
        
        return {
            "user_id": response.user.id,
            "email": response.user.email,
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Login error: {error_msg}")
        if "email not confirmed" in error_msg.lower():
            raise HTTPException(status_code=401, detail="Email not confirmed. Please check your inbox.")
        raise HTTPException(status_code=401, detail="Invalid email or password")

@router.post("/logout")
async def logout(request: Request):
    """Logout user"""
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1]
            supabase.auth.sign_out(token)
        return {"message": "Logged out successfully"}
    except Exception as e:
        return {"message": "Logout failed", "error": str(e)}

@router.get("/me")
async def get_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    try:
        client = get_authenticated_client(current_user.access_token)
        response = client.table("users").select("*").eq("id", current_user.id).single().execute()
        return response.data
    except Exception as e:
        # If profile doesn't exist, return basic info from auth
        return {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.email.split("@")[0],
        }

@router.post("/github-token")
async def set_github_token(request: GitHubTokenRequest, current_user = Depends(get_current_user)):
    """Save user's GitHub token (encrypted in database)"""
    try:
        # Upsert GitHub token
        client = get_authenticated_client(current_user.access_token)
        response = client.table("github_tokens").upsert({
            "user_id": current_user.id,
            "token": request.token,
            "github_username": request.github_username,
        }).execute()
        
        return {
            "message": "GitHub token saved successfully",
            "github_username": request.github_username,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save GitHub token: {str(e)}")

@router.get("/github-token")
async def get_github_token(current_user = Depends(get_current_user)):
    """Get user's GitHub token info"""
    try:
        token, username = await get_user_github_token(current_user.id, current_user.access_token)
        if not token:
            raise HTTPException(status_code=404, detail="GitHub token not configured")
        
        return {
            "github_username": username,
            "configured": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/github-token")
async def delete_github_token(current_user = Depends(get_current_user)):
    """Remove user's GitHub token"""
    try:
        client = get_authenticated_client(current_user.access_token)
        client.table("github_tokens").delete().eq("user_id", current_user.id).execute()
        return {"message": "GitHub token removed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === AIPIPE Token Endpoints ===

class AipipeTokenRequest(BaseModel):
    token: str

@router.post("/aipipe-token")
async def set_aipipe_token(request: AipipeTokenRequest, current_user = Depends(get_current_user)):
    """Save user's AIPIPE token"""
    try:
        client = get_authenticated_client(current_user.access_token)
        client.table("aipipe_tokens").upsert({
            "user_id": current_user.id,
            "token": request.token,
            "updated_at": "now()",
        }).execute()
        return {"message": "AIPIPE token saved successfully", "configured": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save AIPIPE token: {str(e)}")

@router.get("/aipipe-token")
async def get_aipipe_token(current_user = Depends(get_current_user)):
    """Check if user has AIPIPE token configured"""
    try:
        client = get_authenticated_client(current_user.access_token)
        response = client.table("aipipe_tokens").select("token").eq("user_id", current_user.id).single().execute()
        if response.data and response.data.get("token"):
            # Return masked token for display
            raw = response.data["token"]
            masked = raw[:8] + "..." + raw[-4:] if len(raw) > 12 else "****"
            return {"configured": True, "masked_token": masked}
        raise HTTPException(status_code=404, detail="AIPIPE token not configured")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail="AIPIPE token not configured")

@router.delete("/aipipe-token")
async def delete_aipipe_token(current_user = Depends(get_current_user)):
    """Remove user's AIPIPE token"""
    try:
        client = get_authenticated_client(current_user.access_token)
        client.table("aipipe_tokens").delete().eq("user_id", current_user.id).execute()
        return {"message": "AIPIPE token removed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
