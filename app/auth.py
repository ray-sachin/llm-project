# app/auth.py
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, validator
import os, re, time, collections
from dotenv import load_dotenv
from .supabase_client import supabase, supabase_service, verify_user_token, get_user_github_token, get_authenticated_client, get_free_usage_count
from .encryption import encrypt_token, decrypt_token

load_dotenv()

# ── Simple in-memory rate limiter ──
_rate_limit_store: dict[str, list[float]] = collections.defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 15     # requests per window

def _check_rate_limit(key: str):
    """Raise 429 if more than RATE_LIMIT_MAX requests in the window."""
    now = time.time()
    timestamps = _rate_limit_store[key]
    # Prune old entries
    _rate_limit_store[key] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[key]) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment.")
    _rate_limit_store[key].append(now)


def _sanitize(value: str, max_len: int = 500) -> str:
    """Strip dangerous characters and enforce max length."""
    if not value:
        return value
    return value.strip()[:max_len]

router = APIRouter(prefix="/api/auth", tags=["auth"])

class SignUpRequest(BaseModel):
    email: str
    password: str
    username: str

    @validator('email')
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        if len(v) > 254:
            raise ValueError('Email too long')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password too long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain an uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain a number')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain a special character')
        return v

    @validator('username')
    def validate_username(cls, v):
        v = v.strip()
        if not re.match(r'^[a-zA-Z0-9_-]{1,39}$', v):
            raise ValueError('Username must be 1-39 chars: letters, numbers, hyphens, underscores')
        return v

class SignInRequest(BaseModel):
    email: str
    password: str

    @validator('email')
    def validate_email(cls, v):
        return v.strip().lower()[:254]

class GitHubTokenRequest(BaseModel):
    token: str
    github_username: str

    @validator('token')
    def validate_token(cls, v):
        v = v.strip()
        if len(v) < 10 or len(v) > 500:
            raise ValueError('Invalid token length')
        return v

    @validator('github_username')
    def validate_github_username(cls, v):
        v = v.strip()
        if not re.match(r'^[a-zA-Z0-9_-]{1,39}$', v):
            raise ValueError('Invalid GitHub username format')
        return v

class OAuthProfileRequest(BaseModel):
    user_id: str
    email: str
    username: str
    avatar_url: str | None = None
    provider: str = "unknown"
    provider_token: str | None = None

    @validator('email')
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

    @validator('username')
    def validate_username(cls, v):
        v = v.strip()
        if not v:
            return 'user'
        # Allow broader OAuth usernames but sanitize
        v = re.sub(r'[^a-zA-Z0-9_. -]', '', v)[:39]
        return v or 'user'

    @validator('user_id')
    def validate_user_id(cls, v):
        v = v.strip()
        if not v or len(v) > 100:
            raise ValueError('Invalid user ID')
        return v

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
async def sign_up(request: SignUpRequest, req: Request):
    """Register new user"""
    client_ip = req.client.host if req.client else "unknown"
    _check_rate_limit(f"signup:{client_ip}")
    try:
        # Create auth user via Supabase Auth
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "username": request.username,
                },
                "email_redirect_to": f"{frontend_url}/auth/callback",
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
async def sign_in(request: SignInRequest, req: Request):
    """Authenticate user and return session"""
    client_ip = req.client.host if req.client else "unknown"
    _check_rate_limit(f"login:{client_ip}")
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

@router.post("/oauth-profile")
async def sync_oauth_profile(request: OAuthProfileRequest, current_user = Depends(get_current_user)):
    """Create or update user profile for OAuth-authenticated users."""
    try:
        # Ensure the authenticated user matches the profile being synced
        if request.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="User ID mismatch")

        client = get_authenticated_client(current_user.access_token)

        profile_data = {
            "id": current_user.id,
            "email": _sanitize(request.email, 254),
            "username": _sanitize(request.username, 39),
        }

        if request.avatar_url:
            profile_data["avatar_url"] = _sanitize(request.avatar_url, 500)

        # Upsert user profile
        client.table("users").upsert(profile_data).execute()

        return {"message": "Profile synced successfully", "username": request.username}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync profile: {str(e)}")

@router.post("/github-token")
async def set_github_token(request: GitHubTokenRequest, current_user = Depends(get_current_user)):
    """Save user's GitHub token (encrypted at rest)"""
    try:
        # Encrypt token before storing
        encrypted = encrypt_token(request.token)
        client = get_authenticated_client(current_user.access_token)
        response = client.table("github_tokens").upsert({
            "user_id": current_user.id,
            "token": encrypted,
            "github_username": _sanitize(request.github_username, 39),
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

    @validator('token')
    def validate_token(cls, v):
        v = v.strip()
        if len(v) < 10 or len(v) > 2000:
            raise ValueError('Invalid token length')
        return v

@router.post("/aipipe-token")
async def set_aipipe_token(request: AipipeTokenRequest, current_user = Depends(get_current_user)):
    """Save user's AIPIPE token (encrypted at rest)"""
    try:
        encrypted = encrypt_token(request.token)
        client = get_authenticated_client(current_user.access_token)
        client.table("aipipe_tokens").upsert({
            "user_id": current_user.id,
            "token": encrypted,
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
            # Decrypt then mask for display
            raw = decrypt_token(response.data["token"])
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


@router.get("/free-trial-status")
async def get_free_trial_status(current_user = Depends(get_current_user)):
    """Check if user has remaining free trial requests."""
    try:
        count = await get_free_usage_count(current_user.id)
        return {
            "used": count,
            "limit": 1,
            "remaining": max(0, 1 - count),
            "has_free_trial": count < 1,
        }
    except Exception as e:
        return {"used": 0, "limit": 1, "remaining": 1, "has_free_trial": True}
