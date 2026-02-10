# Test OAuth Configuration
# Run this after configuring OAuth in Supabase Dashboard

$PROJECT_ID = "ukiiejnmbvicvpalupyr"
$ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVraWllam5tYnZpY3ZwYWx1cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NDk0MjQsImV4cCI6MjA4NjIyNTQyNH0.2bfIuzuz3_1PWcwr3bnAbxp9DKN_dTxBFLBiqlgC18I"

Write-Host "`n=== Checking OAuth Configuration ===" -ForegroundColor Cyan

# Check auth settings
$headers = @{
    "apikey" = $ANON_KEY
}

Write-Host "`nFetching auth settings..." -ForegroundColor Yellow
$settings = Invoke-RestMethod -Uri "https://$PROJECT_ID.supabase.co/auth/v1/settings" -Headers $headers

Write-Host "`n✓ GoTrue Version: $($settings.'version' ?? 'N/A')" -ForegroundColor Green

Write-Host "`n=== External Providers ===" -ForegroundColor Cyan
Write-Host "  Email:  $(if ($settings.external.email) { '✓ Enabled' } else { '✗ Disabled' })" -ForegroundColor $(if ($settings.external.email) { 'Green' } else { 'Red' })
Write-Host "  GitHub: $(if ($settings.external.github) { '✓ Enabled' } else { '✗ Disabled' })" -ForegroundColor $(if ($settings.external.github) { 'Green' } else { 'Red' })
Write-Host "  Google: $(if ($settings.external.google) { '✓ Enabled' } else { '✗ Disabled' })" -ForegroundColor $(if ($settings.external.google) { 'Green' } else { 'Red' })

Write-Host "`n=== Configuration Status ===" -ForegroundColor Cyan
Write-Host "  Disable Signup: $(if ($settings.disable_signup) { '✓ Yes' } else { '✗ No (Signups allowed)' })" -ForegroundColor $(if ($settings.disable_signup) { 'Red' } else { 'Green' })
Write-Host "  Email Auto-confirm: $(if ($settings.mailer_autoconfirm) { '✓ Yes (No email required)' } else { '✗ No (Email verification required)' })" -ForegroundColor $(if ($settings.mailer_autoconfirm) { 'Green' } else { 'Yellow' })

if ($settings.external.github -and $settings.external.google) {
    Write-Host "`n✅ OAuth is FULLY CONFIGURED! Ready to test." -ForegroundColor Green
    Write-Host "   → Go to http://localhost:5173/login" -ForegroundColor Cyan
    Write-Host "   → Click 'Sign in with Google' or 'Sign in with GitHub'" -ForegroundColor Cyan
} elseif ($settings.external.github -or $settings.external.google) {
    Write-Host "`n⚠️  OAuth is PARTIALLY configured." -ForegroundColor Yellow
    if (-not $settings.external.github) {
        Write-Host "   → GitHub OAuth is NOT enabled yet" -ForegroundColor Red
    }
    if (-not $settings.external.google) {
        Write-Host "   → Google OAuth is NOT enabled yet" -ForegroundColor Red
    }
    Write-Host "`nOpen: https://supabase.com/dashboard/project/$PROJECT_ID/auth/providers" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ OAuth is NOT configured." -ForegroundColor Red
    Write-Host "`nFollow: .\SETUP_OAUTH.md" -ForegroundColor Yellow
    Write-Host "Or open: https://supabase.com/dashboard/project/$PROJECT_ID/auth/providers" -ForegroundColor Cyan
}

Write-Host ""
