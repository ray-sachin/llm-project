# OAuth Setup Guide - 5 Minutes

Everything is coded and ready. You just need to configure the OAuth providers in Supabase Dashboard (I've automated everything that CAN be automated).

## Browser Windows Opened

I've opened these pages for you:

1. **Auth Providers** - https://supabase.com/dashboard/project/ukiiejnmbvicvpalupyr/auth/providers
2. **URL Configuration** - https://supabase.com/dashboard/project/ukiiejnmbvicvpalupyr/auth/url-configuration

---

## Step 1: Configure URLs (2 clicks)

**On the URL Configuration page:**

1. Set **Site URL** to: `http://localhost:5173`
2. Add to **Redirect URLs**: `http://localhost:5173/auth/callback`
3. Click **Save**

---

## Step 2: Enable GitHub OAuth (2 minutes)

**On the Auth Providers page:**

1. Toggle **GitHub** to ON
2. Create a GitHub OAuth App:
   - Go to: https://github.com/settings/developers
   - Click "New OAuth App"
   - **Application name**: `LLM Deploy Platform (Dev)`
   - **Homepage URL**: `http://localhost:5173`
   - **Authorization callback URL**: `https://ukiiejnmbvicvpalupyr.supabase.co/auth/v1/callback`
   - Click "Register application"
   - Generate a **Client Secret**
3. Copy **Client ID** and **Client Secret** → paste into Supabase
4. Under **Scopes**, check: `repo`, `read:user`, `user:email`
5. Click **Save**

---

## Step 3: Enable Google OAuth (2 minutes)

**On the Auth Providers page:**

1. Toggle **Google** to ON
2. Create Google OAuth credentials:
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "OAuth client ID"
   - **Application type**: Web application
   - **Name**: `LLM Deploy Platform (Dev)`
   - **Authorized redirect URIs**: `https://ukiiejnmbvicvpalupyr.supabase.co/auth/v1/callback`
   - Click "Create"
   - Copy **Client ID** and **Client Secret**
3. Paste **Client ID** and **Client Secret** into Supabase
4. Click **Save**

---

## What's Already Done (By Me)

✅ **Frontend:**
- OAuth buttons added to Login/Signup pages with Google & GitHub logos
- AuthCallback page handles OAuth redirects
- Automatically stores GitHub token when user logs in with GitHub
- Email verification redirect configured

✅ **Backend:**
- `POST /api/auth/oauth-profile` endpoint syncs OAuth user data
- GitHub token auto-saved with proper scopes
- Email redirect URL configured (`http://localhost:5173/auth/callback`)
- Rate limiting, encryption, CORS, security headers

✅ **UI Fixes:**
- Dashboard button no longer stretches full-width
- History "Refresh All" and "Clear All" buttons inline with heading
- All buttons properly sized and responsive
- Mobile breakpoints added

✅ **Security:**
- AES-256 Fernet encryption for tokens at rest
- Input validation with Pydantic
- Rate limiting (15 req/min per IP/endpoint)
- CORS restricted to localhost origins
- Security headers (X-Frame-Options, CSP, etc.)
- Backwards-compatible token decryption

---

## After Setup

Restart the frontend dev server to pick up the new Supabase env vars:

```powershell
cd frontend
npm run dev
```

Then test:
1. Go to http://localhost:5173/login
2. Click "Sign in with Google" or "Sign in with GitHub"
3. You'll be redirected to the OAuth provider → back to your app
4. If using GitHub, your token and username are auto-saved

---

**Why I can't do this automatically:**

The Supabase Management API requires a Management API token (NOT the service_role key) which can only be generated from the Dashboard under Settings → Access Tokens. Once you create that token, I could automate this too, but it's faster to just do these 5 clicks.
