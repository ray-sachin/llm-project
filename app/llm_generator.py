import os
import base64
import mimetypes
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize OpenAI (aiPipe endpoint)
client = OpenAI(
    api_key=os.getenv("AIPIPE_TOKEN"),
    base_url="https://aipipe.org/openai/v1"  # Critical for aiPipe!
)

TMP_DIR = Path("/tmp/llm_attachments")
TMP_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# Decode and handle attachments
# ==========================================================
def decode_attachments(attachments):
    """
    attachments: list of dicts, each with either:
        - 'url': "data:<mime>;base64,<b64data>"
        - OR 'content': direct string content
      and 'name' and optional 'mime'
    
    Saves files into /tmp/llm_attachments/<name>
    Returns list of dicts: {"name": name, "path": "/tmp/..", "mime": mime, "size": n}
    """
    saved = []
    for att in attachments or []:
        name = att.get("name") or "attachment"
        path = TMP_DIR / name

        try:
            if "content" in att:
                content = att["content"]
                mime = att.get("mime", "text/plain")
                if mime.startswith("text"):
                    data = content.encode("utf-8")
                else:
                    data = base64.b64decode(content)
                with open(path, "wb") as f:
                    f.write(data)
                saved.append({"name": name, "path": str(path), "mime": mime, "size": len(data)})
                continue

            url = att.get("url", "")
            if url.startswith("data:"):
                header, b64data = url.split(",", 1)
                mime = header.split(";")[0].replace("data:", "")
                data = base64.b64decode(b64data)
                with open(path, "wb") as f:
                    f.write(data)
                saved.append({"name": name, "path": str(path), "mime": mime, "size": len(data)})

        except Exception as e:
            print("Failed to decode/save attachment", name, e)

    return saved


def summarize_attachment_meta(saved):
    """
    saved is list from decode_attachments.
    Returns a short human-readable summary string for the prompt.
    """
    summaries = []
    for s in saved:
        nm = s["name"]
        p = s["path"]
        mime = s.get("mime", "")
        try:
            if mime.startswith("text") or nm.endswith((".md", ".txt", ".json", ".csv")):
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    if nm.endswith(".csv"):
                        lines = [next(f).strip() for _ in range(3)]
                        preview = "\\n".join(lines)
                    else:
                        data = f.read(1000)
                        preview = data.replace("\n", "\\n")[:1000]
                summaries.append(f"- {nm} ({mime}): preview: {preview}")
            else:
                summaries.append(f"- {nm} ({mime}): {s['size']} bytes")
        except Exception as e:
            summaries.append(f"- {nm} ({mime}): (could not read preview: {e})")
    return "\\n".join(summaries)


def _strip_code_block(text: str) -> str:
    """If text is inside triple-backticks, return inner contents."""
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    return text.strip()


def generate_readme_fallback(brief: str, checks=None, attachments_meta=None, round_num=1):
    """Fallback README in case LLM fails."""
    checks_text = "\\n".join(checks or [])
    att_text = attachments_meta or ""
    return f"""# Auto-generated README (Round {round_num})

**Project brief:** {brief}

**Attachments:**
{att_text}

**Checks to meet:**
{checks_text}

## Setup
1. Open `index.html` in a browser.
2. No build steps required.

## Notes
This README was generated as a fallback (OpenAI did not return an explicit README).
"""


# ==========================================================
# Enhanced multi-file generator
# ==========================================================
def generate_app_code(brief: str, attachments=None, checks=None, round_num=1, prev_readme=None):
    """
    Generate or revise a multi-file app using the OpenAI Responses API.
    Automatically detects filenames from the brief and parses multiple files from model output.
    """
    saved = decode_attachments(attachments or [])
    attachments_meta = summarize_attachment_meta(saved)

    # Detect expected filenames from the brief
    expected_files = re.findall(r'[\w\-]+\.(?:txt|json|md|svg|html|csv)', brief)
    if not expected_files:
        expected_files = ["index.html", "README.md"]
    expected_list = "\n".join(f"- {f}" for f in expected_files)

    # Round 2 context
    context_note = ""
    if round_num == 2 and prev_readme:
        context_note = f"\n### Previous README.md:\n{prev_readme}\n\nRevise and enhance this project according to the new brief below.\n"

    # LLM Prompt
    user_prompt = f"""
You are a professional full-stack web developer assistant.

### Round
{round_num}

### Task
{brief}

{context_note}

### Attachments (if any)
{attachments_meta}

### Evaluation checks
{checks or []}

### Expected files
The brief mentions or implies these files:
{expected_list}

### Output format rules:
1. You must output **each file separately** using the following format:
   >>> filename: <name.ext>
   (file content here)
   ---END FILE---
2. Include *all files required by the brief* (e.g., ashravan.txt, dilemma.json, etc.).
3. Every file must contain complete, valid content (valid JSON, SVG, HTML, etc.).
4. Do NOT include commentary outside this format.
5. The final output must contain all files in one response.
"""

    # Call OpenAI (aiPipe)
    try:
        response = client.responses.create(
            model="gpt-5",
            input=[
                {"role": "system", "content": "You are a helpful coding assistant that generates structured multi-file projects."},
                {"role": "user", "content": user_prompt}
            ]
        )
        text = response.output_text or ""
        print("✅ Generated multi-file project via aiPipe/OpenAI.")
    except Exception as e:
        print("⚠ OpenAI API failed, using fallback minimal files:", e)
        text = f"""
>>> filename: index.html
<html><body><h1>Fallback App</h1><p>{brief}</p></body></html>
---END FILE---
>>> filename: README.md
# Auto-generated README
This fallback was generated due to API error.
---END FILE---
"""

    # Parse multi-file format
    files = {}
    pattern = re.compile(r">>> filename:\s*(.+?)\n(.*?)(?=\n---END FILE---|$)", re.S)
    matches = pattern.findall(text)
    if matches:
        for fname, content in matches:
            fname = fname.strip()
            content = _strip_code_block(content.strip())
            files[fname] = content
    else:
        # Legacy fallback
        if "---README.md---" in text:
            code_part, readme_part = text.split("---README.md---", 1)
            files["index.html"] = _strip_code_block(code_part)
            files["README.md"] = _strip_code_block(readme_part)
        else:
            files["index.html"] = _strip_code_block(text)
            files["README.md"] = generate_readme_fallback(brief, checks, attachments_meta, round_num)

    print(f"📦 Parsed {len(files)} files from model output: {list(files.keys())}")
    return {"files": files, "attachments": saved}
