# Test App – LLM Code Deployment Project

This project was built as part of the **TDS Project: LLM Code Deployment**.  
It demonstrates how an application can be **automatically generated, updated, and deployed** using an **LLM-assisted backend** integrated with GitHub and GitHub Pages.

---

## 🚀 Overview
The **Test App** is a web project that evolves in multiple rounds through automated build requests:

| Round | Description |
|--------|-------------|
| **Round 1** | Created a simple web app that displays “Hello World”. |
| **Round 2** | Revised existing code and updated README and layout. |
| **Round 3** | Added `about.html` and `styles.css` to enhance the design. |

---

## ⚙️ How to Run the Backend

You can re-run or test the backend locally to verify the build and deployment logic.

### 1️⃣ Create a Virtual Environment
```bash
python -m venv venv
```

Activate it:
- **Windows (CMD / PowerShell):**
  ```bash
  venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

---

### 2️⃣ Install Dependencies
Make sure your `requirements.txt` file is present (it includes FastAPI, PyGithub, and other libs). Then run:
```bash
pip install -r requirements.txt
```

---

### 3️⃣ Start the Server
Run this command from the project root:
```bash
uvicorn app.main:app --reload
```

This starts the backend on `http://127.0.0.1:8000`.

---

### 4️⃣ Verify a Request
To test, you can send a JSON payload using **curl** (like below):

```bash
curl -X POST http://127.0.0.1:8000/api-endpoint   -H "Content-Type: application/json"   -d @round1_request.json
```

Your server will:
- Receive & verify the JSON request  
- Use LLM-assisted code generation  
- Push files to GitHub  
- Enable GitHub Pages  
- Notify the evaluation server automatically

---

## 🧩 Project Structure

```
test-app/
├── index.html        → Main web page  
├── about.html        → About page (added in round 3)  
├── styles.css        → CSS stylesheet  
├── README.md         → Documentation (this file)  
└── LICENSE           → MIT License
```

---

## 🌐 Live Demo

✅ Deployed on **GitHub Pages:**  
🔗 https://ray-sachin.github.io/test-app/

---

## 🧠 Features
- LLM-powered code generation  
- Round-based iterative updates  
- Auto GitHub commit and push  
- MIT license generation  
- GitHub Pages auto-enablement  
- Evaluation callback for validation

---

## 🧾 Example Evaluation Payload

```json
{
  "email": "1your@example.com",
  "task": "test-app",
  "round": 3,
  "nonce": "456def",
  "repo_url": "https://github.com/ray-sachin/test-app",
  "commit_sha": "abc123",
  "pages_url": "https://ray-sachin.github.io/test-app/"
}
```

---

## 🧑‍💻 Author
**Sachin Ray**  
🧩 Project: LLM Code Deployment  

---

## 📜 License
This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

---

## ✅ Status
✔ All rounds completed  
✔ Attachments handled  
✔ GitHub Pages live  
✔ Evaluation callback successful  
✔ Project verified locally and remotely
