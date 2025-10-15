from fastapi import FastAPI, Request, BackgroundTasks
import os, json, base64
from dotenv import load_dotenv
from .llm_generator import generate_app_code, decode_attachments
from .github_utils import (
    create_repo,
    create_or_update_file,
    enable_pages,
    generate_mit_license,
)
from .notify import notify_evaluation_server
from .github_utils import create_or_update_binary_file
from fastapi.routing import APIRoute
import time

load_dotenv()
USER_SECRET = os.getenv("SECRET")
USERNAME = os.getenv("USERCODE")
PROCESSED_PATH = "/tmp/processed_requests.json"

app = FastAPI()
print("main.py loaded")

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

# === Background task ===
def process_request(data):
    round_num = data.get("round", 1)
    task_id = data["task"]
    print(f"⚙ Starting background process for task {task_id} (round {round_num})")

    # Decode attachments (supports both 'url' and 'content')
    attachments = data.get("attachments", [])
    saved_attachments = decode_attachments(attachments)
    print("Attachments saved:", saved_attachments)

    # Step 0: Fetch previous README for round 2 context
    repo = create_repo(task_id, description=f"Auto-generated app for task: {data['brief']}")
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
        prev_readme=prev_readme
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

    # Step 3: Commit generated app files (index.html, README.md)
    for fname, content in files.items():
        create_or_update_file(repo, fname, content, f"Add/Update {fname}")

    # Step 4: Commit MIT license
    mit_text = generate_mit_license()
    create_or_update_file(repo, "LICENSE", mit_text, "Add MIT license")

    # Step 5: GitHub Pages enablement
    if round_num == 1:
        pages_ok = enable_pages(task_id, branch="main")
        pages_url = f"https://{USERNAME}.github.io/{task_id}/" if pages_ok else None
    else:
        pages_ok = True
        pages_url = f"https://{USERNAME}.github.io/{task_id}/"

    # Step 6: Get latest commit SHA
    try:
        commit_sha = repo.get_commits()[0].sha
    except Exception:
        commit_sha = None

    # Step 7: Notify evaluation server
    payload = {
        "email": data["email"],
        "task": data["task"],
        "round": round_num,
        "nonce": data["nonce"],
        "repo_url": repo.html_url,
        "commit_sha": commit_sha,
        "pages_url": pages_url,
    }
    notify_evaluation_server(data["evaluation_url"], payload)

    # Step 8: Save processed request to avoid duplicates
    processed = load_processed()
    key = f"{data['email']}::{data['task']}::round{round_num}::nonce{data['nonce']}"
    processed[key] = payload
    save_processed(processed)

    print(f"✅ Finished round {round_num} for {task_id}")

@app.get("/debug-routes")
def list_routes():
    return [route.path for route in app.routes if isinstance(route, APIRoute)]

@app.get("/")
def read_root():
    print("Received GET /")
    return {"msg": "OK"}

@app.get("/api-endpoint")
async def test_endpoint():
    return {"status": "ok"}

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