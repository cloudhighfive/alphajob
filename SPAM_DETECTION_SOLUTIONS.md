# Spam Detection Solutions for Ashby Job Applications

## Current Issue
Ashby's backend is flagging automated submissions as spam despite comprehensive anti-detection measures including:
- ✅ Persistent Chrome context with real profile
- ✅ Extensive JavaScript anti-detection scripts (webdriver, chrome object, WebGL, plugins, etc.)
- ✅ Human-like typing with random delays (20-50ms per keystroke)
- ✅ Random mouse movements in curved patterns
- ✅ Realistic scrolling behavior
- ✅ Hover before click with random delays
- ✅ Inter-field delays (0.5-1.5 seconds)
- ✅ Form review scrolling before submit

## Why It's Still Detected

Ashby likely uses **backend behavioral analysis** that checks:
1. **Session history**: New Chrome profile = red flag
2. **Form fill timing**: Even with delays, patterns may be too consistent
3. **Mouse acceleration/deceleration**: Real mice don't move at constant speed
4. **IP reputation**: If IP has submitted multiple times, flagged
5. **Hidden honeypot fields**: Bots fill invisible fields
6. **Browser fingerprinting**: Canvas, WebGL, Audio fingerprints
7. **reCAPTCHA v3**: Invisible score-based CAPTCHA (< 0.5 = bot)

## Recommended Solutions

### Option 1: Hybrid Approach (RECOMMENDED)
**Manual warm-up + automated form filling**

```python
# Add this feature to ai_job_bidder.py
def warm_up_session(page, job_url):
    """Let user browse manually first to establish 'human' session"""
    print("🔥 WARM-UP MODE: Browse manually for 30-60 seconds")
    print("   - Click around the page")
    print("   - Read job description")
    print("   - Scroll naturally")
    print("   - Maybe visit company website and come back")
    print("   - Press ENTER when ready to start automation...")
    
    input()  # Wait for user
    
# Then proceed with automation
```

**Benefits**: Session looks legitimate, has natural browsing history, mouse patterns are real

### Option 2: Use Existing Chrome Profile
Instead of temporary profile, use your real Chrome profile:

```python
# Your actual Chrome profile (not temp)
profile_dir = "/Users/cloud/Library/Application Support/Google/Chrome/Default"

browser_context = p.chromium.launch_persistent_context(
    user_data_dir=profile_dir,
    channel="chrome",
    ...
)
```

**Benefits**: Has cookies, browsing history, saved passwords, extensions = looks very real

**Risk**: Automation might mess with your real browser data

### Option 3: Playwright with Undetected Chromedriver
Install undetected-playwright:

```bash
pip install playwright-stealth undetected-playwright
```

```python
from playwright_stealth import stealth_sync

# After creating page
stealth_sync(page)
```

### Option 4: Manual CAPTCHA Solving
Add CAPTCHA detection and pause:

```python
if page.locator('iframe[title*="recaptcha" i]').count() > 0:
    print("🛑 CAPTCHA detected! Please solve manually...")
    print("   Press ENTER when done...")
    input()
```

### Option 5: Rate Limiting
If submitting multiple applications:

```python
# Only apply to 3-5 jobs per day from same IP
# Wait 10-15 minutes between applications
time.sleep(random.uniform(600, 900))  # 10-15 min
```

### Option 6: Residential Proxy
Use rotating residential proxies to avoid IP flagging:

```python
browser_context = p.chromium.launch_persistent_context(
    user_data_dir=profile_dir,
    channel="chrome",
    proxy={
        "server": "http://proxy-server:port",
        "username": "user",
        "password": "pass"
    }
)
```

Cost: ~$50-100/month for good proxies

### Option 7: Two-Stage Automation
1. **Stage 1**: Bot opens page, fills most fields, then STOPS
2. **Human**: Reviews, maybe edits one field, then submits manually
3. **Backend sees**: Human submitted the form (last action was human)

```python
# Add flag to skip submit
AUTO_SUBMIT = False  # Set to False for human verification

if not AUTO_SUBMIT:
    print("\n⏸️  AUTO-SUBMIT DISABLED")
    print("   Please review the form and click Submit manually")
    input("   Press ENTER to close browser...")
```

## Immediate Action Plan

**Try Option 1 (Hybrid) + Option 7 (No Auto-Submit)**

1. Add warm-up browsing period
2. Fill form automatically
3. Let human click Submit button
4. This gives Ashby a mix of bot + human signals = harder to detect

## Long-term Solution

**Option 2 (Real Chrome Profile) + Option 4 (Manual CAPTCHA)**

Use your actual Chrome profile so the session has real history, cookies, and behavioral data. If CAPTCHA appears, solve it manually. This is the most reliable for passing spam detection while still automating 90% of the work.

## Nuclear Option: Manual Application

If all automated approaches fail, Ashby's detection is too sophisticated. Apply manually or find jobs on platforms with weaker detection (Indeed, LinkedIn).
