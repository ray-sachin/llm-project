from fastapi import FastAPI, Request, BackgroundTasks, Depends, HTTPException
import os, json, base64, uuid, re
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .llm_generator import generate_app_code, decode_attachments
from .github_utils import (
    create_repo,
    create_or_update_file,
    enable_pages,
    generate_mit_license,
    batch_commit_files,
)
from .notify import notify_evaluation_server
from .github_utils import create_or_update_binary_file
from .auth import router as auth_router, get_current_user
from .supabase_client import (
    save_project,
    update_project_status,
    get_user_projects,
    get_user_github_token,
    get_user_aipipe_token,
    get_free_usage_count,
    record_free_usage,
    log_project_history,
)
from fastapi.routing import APIRoute
import time

load_dotenv()
USER_SECRET = os.getenv("SECRET")
USERNAME = os.getenv("USERCODE")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")  # Configurable frontend URL
PROCESSED_PATH = "/tmp/processed_requests.json"

# Store for tracking project status (temporary - can use Supabase for persistence)
project_status = {}

app = FastAPI(title="LLM Deployment Platform", version="2.0.0")

# Include auth routes
app.include_router(auth_router)

# Enable CORS — restrict to known origins
_allowed_origins = [
    FRONTEND_URL,  # Production Vercel URL from env var
    "https://madme.vercel.app",  # Production Vercel deployment
    "http://localhost:5173",  # Local dev
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:3000",
]
# Deduplicate and filter empty
_allowed_origins = list({o.rstrip("/") for o in _allowed_origins if o})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

print("✅ Backend loaded - Multi-user platform with Supabase")

# === Persistence for processed requests ===
def load_processed():
    if os.path.exists(PROCESSED_PATH):
        try:
            return json.load(open(PROCESSED_PATH))
        except json.JSONDecodeError:
            return {}
    return {}

def save_processed(data):
    json.dump(data, open(PROCESSED_PATH, "w"), indent=2)

def process_request_with_logging(task_id: str, data: dict):
    """Wrapper around process_request to update status"""
    user_id = data.get("user_id")
    try:
        print(f"\n{'='*60}")
        print(f"📝 Processing task: {task_id}")
        print(f"👤 User: {data.get('github_username')}")
        print(f"📄 Brief: {data['brief'][:60]}...")
        print(f"{'='*60}\n")
        
        project_status[task_id]["status"] = "generating_code"
        
        # Call the main process function and get results
        result = process_request(data)
        
        # Update status in both memory and Supabase
        if result:
            if "repo_url" in result:
                project_status[task_id]["github_url"] = result["repo_url"]
                print(f"📦 GitHub URL: {result['repo_url']}")
            if "pages_url" in result:
                project_status[task_id]["pages_url"] = result["pages_url"]
                print(f"🌐 Pages URL: {result['pages_url']}")
        
        project_status[task_id]["status"] = "completed"
        
        # Record free trial usage only after successful completion
        if data.get("using_free_trial") and user_id:
            import asyncio
            asyncio.run(record_free_usage(user_id, task_id))
            print(f"   🎁 Free trial request recorded for user {user_id}")
        
        # Update Supabase
        if user_id:
            import asyncio
            asyncio.run(update_project_status(
                user_id=user_id,
                task_id=task_id,
                status="completed",
                github_url=project_status[task_id].get("github_url"),
                pages_url=project_status[task_id].get("pages_url"),
                access_token=data.get("access_token")
            ))
        
        print(f"\n✅ Task {task_id} completed successfully!\n")
        
    except Exception as e:
        print(f"\n❌ Task {task_id} failed with error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        project_status[task_id]["status"] = "failed"
        project_status[task_id]["error"] = str(e)
        
        # Update Supabase with error
        if user_id:
            import asyncio
            asyncio.run(update_project_status(
                user_id=user_id,
                task_id=task_id,
                status="failed",
                access_token=data.get("access_token")
            ))

# === Background task ===
def process_request(data):
    round_num = data.get("round", 1)
    task_id = data["task"]
    github_token = data.get("github_token")  # Per-user token
    github_username = data.get("github_username")  # Per-user username
    
    print(f"⚙ Starting background process for task {task_id} (round {round_num})")
    print(f"👤 Using GitHub account: {github_username}")

    # Decode attachments (supports both 'url' and 'content')
    attachments = data.get("attachments", [])
    saved_attachments = decode_attachments(attachments)
    print("Attachments saved:", saved_attachments)

    # Step 0: Fetch previous README for round 2 context
    repo = create_repo(task_id, description=f"Auto-generated app for task: {data['brief']}", github_token=github_token)
    prev_readme = None
    if round_num >= 2:
        try:
            readme = repo.get_contents("README.md")
            prev_readme = readme.decoded_content.decode("utf-8", errors="ignore")
            print(f"📖 Loaded previous README for round {round_num} context.")
        except Exception:
            prev_readme = None

    # Step 1: Generate app code
    gen = generate_app_code(
        brief=data["brief"],
        attachments=attachments,
        checks=data.get("checks", []),
        round_num=round_num,
        prev_readme=prev_readme,
        aipipe_token=data.get("aipipe_token")
    )

    files = gen.get("files", {})
    saved_info = gen.get("attachments", [])

    # Step 2: Commit all attachments (text and binary) for every round
    for att in saved_info:
        try:
            with open(att["path"], "rb") as f:
                content_bytes = f.read()
            if att["mime"].startswith("text") or att["name"].endswith((".md", ".csv", ".json", ".txt", ".html", ".css", ".js")):
                text = content_bytes.decode("utf-8", errors="ignore")
                create_or_update_file(repo, att["name"], text, f"Add attachment {att['name']}")
            else:
                create_or_update_binary_file(repo, att["name"], content_bytes, f"Add binary {att['name']}")
                b64 = base64.b64encode(content_bytes).decode("utf-8")
                create_or_update_file(repo, f"attachments/{att['name']}.b64", b64, f"Backup {att['name']}.b64")
        except Exception as e:
            print("⚠ Attachment commit failed:", e)

    # Step 3: Commit generated app files + LICENSE in a SINGLE commit
    # This prevents multiple GitHub Actions workflow triggers (and email spam)
    all_files = dict(files)  # Copy generated files (index.html, README.md, etc.)
    all_files["LICENSE"] = generate_mit_license()  # Add license to same commit
    batch_commit_files(repo, all_files, f"Update project files (round {round_num})")

    # Step 5: GitHub Pages enablement
    # Always set pages_url since the URL format is predictable
    pages_url = f"https://{github_username}.github.io/{task_id}/"
    if round_num == 1:
        pages_ok = enable_pages(task_id, branch="main", github_token=github_token, github_username=github_username)
        if pages_ok:
            print(f"✅ Pages URL: {pages_url}")
    else:
        print(f"✅ Pages URL (existing): {pages_url}")

    # Step 6: Get latest commit SHA
    try:
        commit_sha = repo.get_commits()[0].sha
    except Exception:
        commit_sha = None

    # Step 7: Build payload for notification/storage
    payload = {
        "email": data["email"],
        "task": data["task"],
        "round": round_num,
        "nonce": data["nonce"],
        "repo_url": repo.html_url,
        "commit_sha": commit_sha,
        "pages_url": pages_url,
    }
    
    # Skip evaluation server notifications - disabled to avoid email spam
    print(f"⏭️  Skipping evaluation server notification (disabled)")

    # Step 8: Save processed request to avoid duplicates
    processed = load_processed()
    key = f"{data['email']}::{data['task']}::round{round_num}::nonce{data['nonce']}"
    processed[key] = payload
    save_processed(processed)

    print(f"✅ Finished round {round_num} for {task_id}")
    
    # Return URLs for status tracking
    return {
        "repo_url": repo.html_url,
        "pages_url": pages_url
    }

@app.get("/debug-routes")
def list_routes():
    return [route.path for route in app.routes if isinstance(route, APIRoute)]

@app.get("/")
def read_root():
    print("Received GET /")
    return {"msg": "OK"}

@app.get("/health")
@app.head("/health")
def health_check():
    """Health check endpoint - supports GET and HEAD for monitoring services"""
    return {"status": "ok", "message": "Backend is running"}

@app.get("/projects")
async def get_projects(current_user = Depends(get_current_user)):
    """Get all projects for the authenticated user"""
    try:
        projects = await get_user_projects(current_user.id, current_user.access_token)
        return projects
    except Exception as e:
        print(f"❌ Error fetching projects: {str(e)}")
        return []

@app.get("/api-endpoint")
async def test_endpoint():
    return {"status": "ok"}

# === Endpoint for frontend ===
@app.post("/deploy")
async def deploy_project(request: Request, background_tasks: BackgroundTasks, current_user = Depends(get_current_user)):
    """Frontend endpoint for submitting new projects (requires authentication)"""
    print(f"📩 Deployment request from user: {current_user.id}")
    
    try:
        form_data = await request.form()
        brief = form_data.get("brief", "")
        checks = form_data.get("checks", "")
        
        if not brief:
            return JSONResponse(status_code=400, content={"error": "Project brief is required"})
        
        # Parse checks if it's a JSON string
        try:
            if isinstance(checks, str) and checks.startswith('['):
                checks_list = json.loads(checks)
            else:
                checks_list = [c.strip() for c in checks.split(',') if c.strip()] if checks else []
        except:
            checks_list = []
        
        # Get user's GitHub token from Supabase
        github_token, github_username = await get_user_github_token(current_user.id, current_user.access_token)
        if not github_token or not github_username:
            return JSONResponse(status_code=400, content={"error": "GitHub token not configured. Please add your GitHub token in settings."})
        
        # Get user's AIPIPE token (user's own token always takes priority)
        user_aipipe_token = await get_user_aipipe_token(current_user.id, current_user.access_token)
        using_free_trial = False
        
        if not user_aipipe_token:
            # No user token — check free trial eligibility
            free_count = await get_free_usage_count(current_user.id)
            server_token = os.getenv("AIPIPE_TOKEN")
            
            if free_count >= 1:
                # Already used the 1 free request
                return JSONResponse(status_code=403, content={
                    "error": "Free trial used. Please add your own AIPIPE token in Settings to continue.",
                    "code": "AIPIPE_TOKEN_REQUIRED",
                    "settings_url": "/settings"
                })
            
            if not server_token:
                # Server has no fallback token either
                return JSONResponse(status_code=403, content={
                    "error": "No AIPIPE token available. Please add your own AIPIPE token in Settings.",
                    "code": "AIPIPE_TOKEN_REQUIRED",
                    "settings_url": "/settings"
                })
            
            # Use server's token for this 1 free request
            using_free_trial = True
            print(f"   🎁 Using free trial request for user {current_user.id}")
        
        print(f"✅ Deployment request accepted")
        print(f"   User: {github_username}")
        print(f"   Brief: {brief[:50]}...")
        print(f"   Checks: {checks_list}")
        
        # Create task ID from brief (this will be the repo name)
        # Use up to 6 words from the brief for a clean, readable repo name
        words = re.sub(r'[^a-zA-Z0-9\s]', '', brief).split()
        slug_words = [w.lower() for w in words[:6]]
        sanitized_brief = "-".join(slug_words) if slug_words else ""
        # GitHub repo names max 100 chars; keep it safe at 80
        sanitized_brief = sanitized_brief[:80].rstrip("-")
        task_id = sanitized_brief or f"app-{uuid.uuid4().hex[:8]}"
        
        # Prepare data for processing
        request_data = {
            "task": task_id,
            "brief": brief,
            "checks": checks_list,
            "user_id": current_user.id,
            "email": current_user.email,
            "github_token": github_token,
            "github_username": github_username,
            "round": 1,
            "nonce": uuid.uuid4().hex[:8],
            "attachment": [],
            "access_token": current_user.access_token,
            "aipipe_token": user_aipipe_token,  # None = server fallback inside generator
            "using_free_trial": using_free_trial,
        }
        
        # Store initial status
        project_status[task_id] = {
            "user_id": current_user.id,
            "status": "processing",
            "brief": brief,
            "checks": checks_list,
            "created_at": str(__import__('datetime').datetime.now()),
            "github_url": None,
            "pages_url": None,
            "error": None
        }
        
        # Save to Supabase
        await save_project(
            user_id=current_user.id,
            task_id=task_id,
            brief=brief,
            checks=checks_list,
            status="processing",
            round_num=1,
            access_token=current_user.access_token
        )
        
        # Schedule background processing
        background_tasks.add_task(process_request_with_logging, task_id, request_data)
        
        print(f"✅ Task {task_id} enqueued for processing")
        
        return {
            "task_id": task_id,
            "check_status_url": f"/status/{task_id}"
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

# === Main endpoint ===
@app.post("/api-endpoint")
async def receive_request(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    print("📩 Received request:", data)

    # Step 0: Verify secret
    if data.get("secret") != USER_SECRET:
        print("❌ Invalid secret received.")
        return {"error": "Invalid secret"}

    processed = load_processed()
    key = f"{data['email']}::{data['task']}::round{data['round']}::nonce{data['nonce']}"

    # Duplicate detection
    if key in processed:
        print(f"⚠ Duplicate request detected for {key}. Re-notifying only.")
        prev = processed[key]
        notify_evaluation_server(data.get("evaluation_url"), prev)
        return {"status": "ok", "note": "duplicate handled & re-notified"}

    # Schedule background task (non-blocking)
    background_tasks.add_task(process_request, data)

    # Immediate HTTP 200 acknowledgment
    return {"status": "accepted", "note": f"processing round {data['round']} started"}


# === Status & Debugging Endpoints ===
@app.get("/status/{task_id}")
def get_task_status(task_id: str):
    """Get the status of a project deployment"""
    # If we have it in memory, return it
    if task_id in project_status:
        return {
            "task_id": task_id,
            **project_status[task_id]
        }
    
    # Otherwise, try to check if the GitHub repo exists
    # This handles cases where the backend restarted after task completion
    try:
        from github import Github, GithubException
        import os
        github_token = os.getenv("GITHUB_TOKEN")
        username = os.getenv("USERCODE")
        
        if github_token and username:
            g = Github(github_token)
            user = g.get_user()
            
            try:
                # Check if repo exists
                repo = user.get_repo(task_id)
                # Repo exists, so task is completed
                github_url = repo.html_url
                pages_url = f"https://{username}.github.io/{task_id}/"
                
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "github_url": github_url,
                    "pages_url": pages_url,
                    "brief": "",
                    "checks": [],
                    "created_at": "",
                    "error": None
                }
            except GithubException:
                # Repo doesn't exist, might still be processing or failed
                pass
    except Exception as e:
        print(f"Error checking GitHub for task {task_id}: {e}")
    
    # Not found anywhere
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=404, content={"error": "Task not found", "task_id": task_id})

@app.get("/all-tasks")
def get_all_tasks():
    """Get status of all tasks for debugging"""
    return {
        "total_tasks": len(project_status),
        "tasks": project_status
    }

@app.get("/logs")
def get_logs():
    """Get recent logs - useful for debugging"""
    return {
        "message": "Check the backend terminal/console for detailed logs",
        "note": "Backend logs are printed to stdout in real-time",
        "status": "Backend is running with logging enabled"
    }

@app.get("/config")
def get_config():
    """Check configuration (safe values only)"""
    return {
        "github_username": os.getenv("USERCODE", "NOT SET"),
        "github_token_set": bool(os.getenv("GITHUB_TOKEN")),
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "environment": "development" if os.getenv("DEBUG") else "production"
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server...")
    print("📍 API available at: http://localhost:8000")
    print("📚 Documentation at: http://localhost:8000/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)