# app/supabase_client.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from .encryption import decrypt_token

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Initialize Supabase client (anon key — used for auth operations)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Service client (for backend operations with full permissions)
# Falls back to anon key if service key is missing/invalid
_service_key = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_ANON_KEY
supabase_service: Client = create_client(SUPABASE_URL, _service_key)


def get_authenticated_client(access_token: str) -> Client:
    """Create a Supabase client authenticated with a user's access token.
    This allows database operations scoped by RLS policies."""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)
    return client


def get_user_id_from_token(token: str):
    """Extract user ID from JWT token (for verification)"""
    try:
        from jose import jwt
        decoded = jwt.get_unverified_claims(token)
        return decoded.get("sub")
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

async def verify_user_token(token: str):
    """Verify JWT token from Supabase"""
    try:
        user = supabase.auth.get_user(token)
        return user
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

async def get_user_github_token(user_id: str, access_token: str = None):
    """Get user's GitHub token from database (decrypted)"""
    try:
        client = get_authenticated_client(access_token) if access_token else supabase_service
        response = client.table("github_tokens").select("token, github_username").eq("user_id", user_id).single().execute()
        if response.data:
            raw_token = response.data["token"]
            # Decrypt the token (handles both encrypted and legacy plaintext)
            plaintext_token = decrypt_token(raw_token)
            return plaintext_token, response.data["github_username"]
        return None, None
    except Exception as e:
        print(f"Error fetching GitHub token: {e}")
        return None, None

async def save_project(user_id: str, task_id: str, brief: str, checks: dict, status: str, github_url: str = None, pages_url: str = None, round_num: int = 1, access_token: str = None):
    """Save project to database"""
    try:
        client = get_authenticated_client(access_token) if access_token else supabase_service
        response = client.table("projects").insert({
            "user_id": user_id,
            "task_id": task_id,
            "brief": brief,
            "checks": checks,
            "status": status,
            "github_url": github_url,
            "pages_url": pages_url,
            "round": round_num,
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error saving project: {e}")
        return None

async def update_project_status(user_id: str, task_id: str, status: str, github_url: str = None, pages_url: str = None, access_token: str = None):
    """Update project status"""
    try:
        client = get_authenticated_client(access_token) if access_token else supabase_service
        data_to_update = {
            "status": status,
            "updated_at": "now()"
        }
        if github_url:
            data_to_update["github_url"] = github_url
        if pages_url:
            data_to_update["pages_url"] = pages_url
        
        response = client.table("projects").update(data_to_update).eq("user_id", user_id).eq("task_id", task_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating project: {e}")
        return None

async def get_user_projects(user_id: str, access_token: str = None):
    """Get all projects for a user"""
    try:
        client = get_authenticated_client(access_token) if access_token else supabase_service
        response = client.table("projects").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return []

async def log_project_history(user_id: str, project_id: str, action: str, status: str, error_message: str = None, access_token: str = None):
    """Log project action to history"""
    try:
        client = get_authenticated_client(access_token) if access_token else supabase_service
        response = client.table("project_history").insert({
            "user_id": user_id,
            "project_id": project_id,
            "action": action,
            "status": status,
            "error_message": error_message,
        }).execute()
        return True
    except Exception as e:
        print(f"Error logging history: {e}")
        return False

async def get_user_aipipe_token(user_id: str, access_token: str = None):
    """Get user's AIPIPE token from database (decrypted)"""
    try:
        client = get_authenticated_client(access_token) if access_token else supabase_service
        response = client.table("aipipe_tokens").select("token").eq("user_id", user_id).single().execute()
        if response.data:
            raw_token = response.data["token"]
            return decrypt_token(raw_token)
        return None
    except Exception as e:
        print(f"Error fetching AIPIPE token: {e}")
        return None


# === Free LLM Usage Tracking ===

async def get_free_usage_count(user_id: str) -> int:
    """Get how many free LLM requests a user has made (using server's AIPIPE token)."""
    try:
        response = supabase_service.table("free_llm_usage").select("id", count="exact").eq("user_id", user_id).execute()
        return response.count if response.count is not None else 0
    except Exception as e:
        print(f"Error checking free usage: {e}")
        return 0


async def record_free_usage(user_id: str, task_id: str = None):
    """Record that a user consumed a free LLM request."""
    try:
        supabase_service.table("free_llm_usage").insert({
            "user_id": user_id,
            "task_id": task_id,
        }).execute()
        return True
    except Exception as e:
        print(f"Error recording free usage: {e}")
        return False
