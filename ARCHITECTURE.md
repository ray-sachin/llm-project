# LLM Deployment Platform - Architecture

Technical deep-dive into the multi-user SaaS platform architecture, design decisions, and how components interact.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Frontend Architecture](#frontend-architecture)
4. [Backend Architecture](#backend-architecture)
5. [Database Design](#database-design)
6. [Authentication Flow](#authentication-flow)
7. [Deployment Flow](#deployment-flow)
8. [Security Architecture](#security-architecture)
9. [Scalability Considerations](#scalability-considerations)
10. [Integration Points](#integration-points)

---

## System Overview

The LLM Deployment Platform is a three-tier SaaS application:

```
┌─────────────────────────────────────────────────┐
│          Presentation Layer (Frontend)           │
│  React 19 + TypeScript (Client-side State)       │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/REST API + Bearer JWT
┌──────────────────▼──────────────────────────────┐
│       Application Layer (Backend)                │
│  FastAPI + Async Python (Server-side Logic)     │
└──────────────────┬──────────────────────────────┘
                   │ PostgreSQL Driver
┌──────────────────▼──────────────────────────────┐
│          Data Layer (Supabase)                   │
│  PostgreSQL + Authentication + Storage           │
└─────────────────────────────────────────────────┘
```

---

## Architecture Diagram

### High-Level Component Interaction

```
User Browser
    │
    ├─→ [Frontend SPA]
    │   ├─ Login/Signup
    │   ├─ Settings (GitHub config)
    │   ├─ Dashboard
    │   ├─ Create Project
    │   └─ History
    │
    └─→ HTTP/REST ──→ [Backend API]
                      ├─ /api/auth/* (authentication)
                      ├─ /deploy (project creation)
                      ├─ /projects (list user projects)
                      ├─ /status/{id} (check status)
                      └─ /health (monitoring)
                      │
                      └─→ [External Services]
                          ├─ GitHub API (repo ops)
                          ├─ AIPIPE API (code gen)
                          └─ Supabase API
                              ├─ PostgreSQL (data)
                              ├─ Auth Service
                              └─ Storage
```

---

## Frontend Architecture

### State Management

**localStorage-based approach for simplicity:**
```typescript
// Authentication tokens (persisted in localStorage)
{
  access_token: "JWT_TOKEN",
  refresh_token: "REFRESH_TOKEN",
  user_id: "UUID"
}
```

### Page Components

| Page | Purpose | Auth Required |
|------|---------|--------------|
| `Login.tsx` | Email/password authentication | ❌ |
| `Signup.tsx` | New user registration | ❌ |
| `Settings.tsx` | GitHub token configuration | ✅ |
| `Dashboard.tsx` | Projects overview | ✅ |
| `CreateProject.tsx` | Submit new project | ✅ |
| `History.tsx` | Deployment history | ✅ |

### API Client Pattern

```typescript
// Axios instance with auto-attached JWT
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-redirect on 401 Unauthorized
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Routing Strategy

```
/login                    (Public - redirects if logged in)
/signup                   (Public - redirects if logged in)
/                         (Protected - Dashboard)
/create                   (Protected - Create Project)
/history                  (Protected - History)
/settings                 (Protected - Settings)
```

### Protected Route Implementation

```typescript
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
```

---

## Backend Architecture

### Layered Design

```
┌─────────────────────────────────────────────┐
│      Route Handlers (FastAPI)                │
│  /api/auth/*, /deploy, /projects, /status   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      Business Logic Layer                    │
│  Authorization, Validation, Orchestration    │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      Integration Layer                       │
│  GitHub API, AIPIPE API, Supabase SDK       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      External Services                       │
│  GitHub, AIPIPE, Supabase                    │
└─────────────────────────────────────────────┘
```

### Key Modules

**auth.py** - Authentication endpoints
```python
POST  /api/auth/signup      # Create user + db entry
POST  /api/auth/login       # Authenticate + return JWT
POST  /api/auth/logout      # Invalidate session
GET   /api/auth/me          # Current user profile
POST  /api/auth/github-token    # Save encrypted token
GET   /api/auth/github-token    # Retrieve username
DELETE /api/auth/github-token   # Remove token
```

**main.py** - Core application & routes
```python
POST  /deploy               # Create project (needs auth)
GET   /projects             # List user projects
GET   /status/{task_id}     # Check deployment status
GET   /health              # Health check (no auth)
```

**github_utils.py** - GitHub operations
```python
create_repo()              # Create GitHub repo
create_or_update_file()    # Commit files
enable_pages()             # Enable GitHub Pages
batch_commit_files()       # Atomic batch operations
```

**llm_generator.py** - LLM integration
```python
generate_app_code()        # Call AIPIPE API
decode_attachments()       # Process uploaded files
```

**supabase_client.py** - Database operations
```python
save_project()             # Insert project record
update_project_status()    # Update after completion
get_user_projects()        # List user's projects
log_project_history()      # Audit trail
get_user_github_token()    # Retrieve encrypted token
```

### Async Request Flow

```
User Request
    │
    ▼
[FastAPI Route Handler]
    │
    ├─→ [Authentication]
    │   └─→ Verify JWT token
    │
    ├─→ [Validation]
    │   └─→ Check input parameters
    │
    ├─→ [Business Logic]
    │   ├─→ Generate project ID
    │   └─→ Save to Supabase
    │
    ├─→ [Background Task]
    │   └─→ Schedule processing
    │       ├─→ Call AIPIPE for code gen
    │       ├─→ Create GitHub repo
    │       ├─→ Commit code
    │       ├─→ Enable GitHub Pages
    │       └─→ Update status in DB
    │
    └─→ [Response to Client]
        └─→ Return task_id + initial status
```

---

## Database Design

### Schema Overview

```sql
-- Users (linked to Supabase Auth)
users
  ├─ id (UUID) - Primary Key [FK: auth.users]
  ├─ email (string) - unique
  ├─ username (string) - unique
  ├─ created_at (timestamp)
  └─ updated_at (timestamp)

-- GitHub Tokens (per-user, encrypted)
github_tokens
  ├─ id (UUID) - Primary Key
  ├─ user_id (UUID) [FK: users.id]
  ├─ token (encrypted string)
  ├─ github_username (string)
  ├─ created_at (timestamp)
  ├─ expires_at (timestamp nullable)
  └─ unique(user_id)  -- Only one token per user

-- Project Records
projects
  ├─ id (UUID) - Primary Key
  ├─ user_id (UUID) [FK: users.id]
  ├─ task_id (string) - project name
  ├─ brief (string) - description
  ├─ checks (JSONB) - requirements
  ├─ status (enum) - pending/processing/completed/failed
  ├─ github_url (string nullable)
  ├─ pages_url (string nullable)
  ├─ round (integer) - iteration count
  ├─ created_at (timestamp)
  ├─ updated_at (timestamp)
  └─ unique(user_id, task_id)  -- One project per user with same name

-- Project History (Audit Trail)
project_history
  ├─ id (UUID) - Primary Key
  ├─ project_id (UUID) [FK: projects.id]
  ├─ user_id (UUID) [FK: users.id]
  ├─ action (string)
  ├─ status (string)
  ├─ error_message (string nullable)
  └─ created_at (timestamp)
```

### Indexes for Performance

```sql
-- For user-specific queries
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_github_tokens_user_id ON github_tokens(user_id);
CREATE INDEX idx_project_history_user_id ON project_history(user_id);

-- For lookup queries
CREATE INDEX idx_projects_task_id ON projects(task_id);
CREATE INDEX idx_project_history_project_id ON project_history(project_id);

-- For sorting
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX idx_project_history_created_at ON project_history(created_at DESC);
```

### Row-Level Security (RLS) Policies

```sql
-- Projects: Users can only view/modify their own
CREATE POLICY projects_select ON projects
  FOR SELECT USING (auth.uid() = user_id);

-- GitHub Tokens: Users can only view/modify their own
CREATE POLICY github_tokens_select ON github_tokens
  FOR SELECT USING (auth.uid() = user_id);

-- History: Users can only view their own
CREATE POLICY history_select ON project_history
  FOR SELECT USING (auth.uid() = user_id);
```

---

## Authentication Flow

### Sign Up Flow

```
[User Input] → POST /api/auth/signup
                    │
                    ├─→ Validate email (not exists)
                    ├─→ Call Supabase Auth: signUpWithPassword()
                    │   │
                    │   ├─→ Hash password
                    │   ├─→ Create auth.users record
                    │   └─→ Return JWT + refresh token
                    │
                    ├─→ Create user profile in public.users table
                    │   └─→ Insert: id, email, username
                    │
                    └─→ Return: { access_token, refresh_token, user_id }
                        │
                        └─→ [Frontend] Store in localStorage
```

### Login Flow

```
[User Input] → POST /api/auth/login
                    │
                    ├─→ Validate email exists
                    ├─→ Call Supabase Auth: signInWithPassword()
                    │   │
                    │   ├─→ Verify password hash
                    │   └─→ Return JWT + refresh token
                    │
                    └─→ Return: { access_token, refresh_token, user_id }
                        │
                        └─→ [Frontend] Store in localStorage
```

### Request Authorization

```
[Frontend] GET /projects
           Header: Authorization: Bearer <JWT>
                    │
                    ▼
[Backend] Middleware: get_current_user(Request)
                    │
                    ├─→ Extract token from header
                    ├─→ Verify JWT signature (via Supabase)
                    ├─→ Check token not expired
                    │
                    └─→ Return: user_id or raise 401

[Backend] Route Handler
           Receives: current_user from dependency
                    │
                    ├─→ Query: SELECT * FROM projects WHERE user_id = current_user.id
                    │
                    └─→ Return: Only current user's projects
```

---

## Deployment Flow

### Submission to Completion

```
1. Frontend: POST /deploy
             {
               brief: "Build a todo app",
               checks: ["responsive", "dark mode"],
               attachments: [File, File]
             }

2. Backend: validate_request()
            │
            ├─→ Validate user authenticated
            ├─→ Check GitHub token configured
            ├─→ Validate brief provided
            └─→ Save project to DB (status: processing)

3. Backend: Background Task
            ├─→ Get GitHub token from Supabase
            ├─→ Call AIPIPE API: generate code
            │   {
            │     brief: "...",
            │     attachments: "...",
            │     output: { files: {...} }
            │   }
            │
            ├─→ Create GitHub repo
            │   api.repos.create(
            │     name=task_id,
            │     description=brief,
            │     private=False
            │   )
            │
            ├─→ Commit generated files
            │   batch_commit_files(
            │     [file1, file2, ...],
            │     message=f"Round 1: {brief}"
            │   )
            │
            ├─→ Enable GitHub Pages
            │   repo.enable_pages(
            │     source="main",
            │     path="/"
            │   )
            │
            └─→ Update project status
                update_project_status(
                  project_id=id,
                  status="completed",
                  github_url=repo.html_url,
                  pages_url=f"{username}.github.io/{task_id}/"
                )

4. Frontend: Auto-refresh /projects
             ├─→ See github_url + pages_url populated
             └─→ Click link to view live site
```

---

## Security Architecture

### Token Management

```
┌─────────────────────────────────────┐
│  Supabase Auth (JWT Issuer)         │
│  ├─ Issues JWT on login/signup      │
│  ├─ Contains user_id + exp time     │
│  └─ Signed with secret key          │
└────────────┬────────────────────────┘
             │ Token stored in localStorage
             │ (XSS Risk ⚠️ - see Mitigation)
             │
┌────────────▼────────────────────────┐
│  Browser LocalStorage                │
│  ├─ access_token (JWT)               │
│  ├─ refresh_token (for renewal)      │
│  └─ user_id (for quick access)       │
└────────────┬────────────────────────┘
             │ Included in API request
             │ Header: Authorization: Bearer <token>
             │
┌────────────▼───────────────────────────┐
│  Backend Route Handler                  │
│  ├─ Extract token from header           │
│  ├─ Call get_current_user(request)      │
│  ├─ Verify JWT signature via Supabase   │
│  ├─ Check authorization (RLS)           │
│  └─ Process request or return 401       │
└─────────────────────────────────────────┘
```

### GitHub Token Encryption

```
┌──────────────────────────────┐
│  User Input: PAT             │
│  "ghp_abc123xyz..."          │
└────────────┬─────────────────┘
             │
             ├─→ Encrypt with cryptography library
             │   (AES-256-GCM via Supabase)
             │
             └─→ Encrypted bytes stored in DB
                 Looks like: "encrypted:abc123..."
                 
When retrieving:
             ├─→ Fetch encrypted from DB
             ├─→ Decrypt using server key
             └─→ Use plain token for GitHub API
                 (never returned to frontend)
```

### Request Validation

```
Every /deploy request validates:
  ✓ JWT token valid + not expired
  ✓ User has GitHub token configured
  ✓ Brief is provided (non-empty)
  ✓ Checks array format valid
  ✓ File uploads under size limit
  ✓ Rate limit not exceeded
  ✗ Missing any → return 400 Bad Request
  ✗ Unauthorized → return 401
  ✗ Rate limited → return 429
```

### XSS Protection

⚠️ **Issue**: JWT stored in localStorage is vulnerable to XSS attacks

**Current**: Browser XSS can steal token → attacker makes API calls

**Mitigation Options**:
1. **Next**: Consider httpOnly cookies (requires same-origin backend)
2. **Future**: Implement CSRF tokens for state-changing operations
3. **Best Practice**: Regular security audits + CSP headers

---

## Scalability Considerations

### Load Handling

```
Horizontal Scaling:
  ├─ Stateless backend (multiple instances)
  ├─ Load balancer distributes requests
  ├─ Supabase handles database concurrency
  └─ GitHub API has rate limiting

Vertical Scaling:
  ├─ Async Python (uvicorn workers)
  ├─ Background task queue (Celery - future)
  └─ Database connection pooling (Supabase)
```

### Performance Optimizations

```
Frontend:
  ├─ Code splitting with Vite
  ├─ Lazy loading of routes
  ├─ Caching strategy (ETag headers)
  └─ CDN for static assets

Backend:
  ├─ Async/await for I/O operations
  ├─ Database indexes on frequently queried fields
  ├─ Query optimization (SELECT specific columns)
  └─ Caching layer (Redis - future)

Database:
  ├─ Connection pooling
  ├─ Indexes on foreign keys + filters
  ├─ Query result caching (24h TTL)
  └─ Slow query logging
```

### Rate Limiting Strategy

```
Per-user limits (future):
  ├─ 10 projects per day (default)
  ├─ 100 API calls per hour
  ├─ 50MB total file uploads per day
  └─ Sliding window counter in Redis

Global limits:
  ├─ GitHub API: 5000 calls/hour per token
  ├─ AIPIPE API: Contact for limits
  └─ Supabase: Depends on plan
```

---

## Integration Points

### GitHub API Integration

```python
# Authentication
github_token = user.github_token  # Encrypted in DB
g = Github(github_token)          # Decrypted on use
user = g.get_user()

# Create repository
repo = user.create_repo(
    name=task_id,
    description=brief,
    private=False,
    auto_init=False
)

# Commit files
commit = batch_commit_files(
    repo=repo,
    files=[...],
    message=f"Round {round}: {brief}"
)

# Enable Pages
repo.edit(
    has_pages=True,
    pages={
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
)
```

### AIPIPE API Integration

```python
response = aipipe_api.generate(
    prompt=brief,
    attachments=[...],
    model="llama-2",
    temperature=0.7,
    max_tokens=4000
)

generated_code = response['code']
files = parse_response(generated_code)
# Returns: { 'index.html': '...', 'app.js': '...', ... }
```

### Supabase Integration

```python
# Authentication
user = supabase.auth.sign_up(
    email=email,
    password=password
)

# Database operations
supabase.table('projects').insert({
    'user_id': user.id,
    'task_id': task_id,
    'brief': brief,
    'status': 'processing'
})

supabase.table('projects').update({
    'status': 'completed',
    'github_url': github_url,
    'pages_url': pages_url
}).eq('id', project_id)

# Query with RLS applied
projects = supabase.table('projects').select('*').execute()
# Only returns current user's projects
```

---

## Monitoring & Observability

### Health Checks

```python
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "backend": "running",
        "timestamp": datetime.now()
    }

# Frontend periodically calls /health
// Frontend polls every 30 seconds
setInterval(() => {
  api.healthCheck().then(ok => {
    // Show offline warning if fails
    updateStatus(ok);
  });
}, 30000);
```

### Logging Strategy

```python
import logging

# Application logs
logger.info(f"User {user_id} created project")
logger.error(f"GitHub API error: {error}")
logger.warning(f"Project {id} failed: {reason}")

# Supabase logs
# Accessible in Supabase dashboard
# Includes: API calls, Auth events, query times
```

---

**Last Updated**: February 2026
