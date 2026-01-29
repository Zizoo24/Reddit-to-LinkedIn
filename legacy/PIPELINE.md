# Reddit-to-LinkedIn Pipeline Guide

A complete guide to running the content pipeline locally (without GitHub Actions).

---

## Quick Start

```bash
# One-time setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the full pipeline
python run.py pipeline
```

---

## Pipeline Options

### 1. Manual Execution (Run When You Want)

```bash
# Full pipeline - scan Reddit + generate LinkedIn posts
python run.py pipeline

# Scan only (no AI generation, no API key needed)
python run.py pipeline --no-generate

# Generate more posts
python run.py pipeline --count 5

# Quick scan to see what's trending
python run.py scan --comments
```

### 2. Scheduled Execution (Local Scheduler)

Run the pipeline automatically on a schedule:

```bash
# Run daily at 8 AM
python local_scheduler.py --schedule daily

# Run weekly on Monday at 8 AM
python local_scheduler.py --schedule weekly

# Run twice daily (8 AM and 6 PM)
python local_scheduler.py --schedule twice-daily

# Run every hour (for testing)
python local_scheduler.py --schedule hourly
```

**Keep running in background (Windows):**
```powershell
# Option 1: Start minimized
start /min python local_scheduler.py --schedule daily

# Option 2: Use Task Scheduler (see below)
```

**Keep running in background (Mac/Linux):**
```bash
# Using nohup
nohup python local_scheduler.py --schedule daily &

# Using screen
screen -S linkedin-pipeline
python local_scheduler.py --schedule daily
# Press Ctrl+A, then D to detach
```

### 3. Windows Task Scheduler

For true "set and forget" automation on Windows:

1. Open **Task Scheduler** (search in Start menu)
2. Click **Create Basic Task**
3. Name: "Reddit LinkedIn Pipeline"
4. Trigger: Daily (or Weekly)
5. Time: 8:00 AM (or whenever)
6. Action: Start a Program
7. Program: `python`
8. Arguments: `C:\Users\H\Documents\GitHub\Reddit-to-LinkedIn\run.py pipeline`
9. Start in: `C:\Users\H\Documents\GitHub\Reddit-to-LinkedIn`

### 4. Mac/Linux Cron Job

```bash
# Edit crontab
crontab -e

# Add line for daily at 8 AM:
0 8 * * * cd /path/to/Reddit-to-LinkedIn && python run.py pipeline >> output/cron.log 2>&1

# Weekly on Monday at 8 AM:
0 8 * * 1 cd /path/to/Reddit-to-LinkedIn && python run.py pipeline >> output/cron.log 2>&1
```

---

## Posting to LinkedIn

The system auto-detects which method to use based on your `.env` file.
**Free options are checked first.**

---

### FREE OPTIONS

### Option A: Zapier Webhooks (FREE - Recommended)

**Free tier: 100 tasks/month** - Good for posting a few times per week.

**Setup:**
1. Create account at https://zapier.com
2. Create a new Zap:
   - Trigger: **Webhooks by Zapier** → Catch Hook
   - Action: **LinkedIn** → Create Share Update
3. Copy your webhook URL
4. Add to `.env`:
   ```
   ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/...
   ```

**Usage:**
```bash
python run.py post --text "Your post content here"
python run.py post --file output/linkedin_posts.txt
```

### Option B: Make.com (FREE alternative)

**Free tier: 1000 ops/month** - More generous than Zapier.

**Setup:**
1. Create account at https://make.com
2. Create scenario: Custom Webhook → LinkedIn
3. Copy webhook URL
4. Add to `.env`:
   ```
   MAKE_WEBHOOK_URL=https://hook.make.com/...
   ```

**Usage:**
```bash
python run.py post --method make --text "Posted via Make!"
```

### Option C: LinkedIn Direct API (FREE but complex)

**Free but tokens expire every 60 days** - Requires OAuth refresh.

**Setup:**
1. Go to https://www.linkedin.com/developers/apps
2. Create a new app
3. Request **w_member_social** permission
4. Complete OAuth2 flow to get access token
5. Add to `.env`:
   ```
   LINKEDIN_ACCESS_TOKEN=your_token_here
   ```

**Usage:**
```bash
python run.py post --method linkedin --text "Your post"
```

---

### PAID OPTIONS

### Option D: Ayrshare ($49/mo+)

Easiest setup if you're willing to pay. No token refresh needed.

**Setup:**
1. Sign up at https://www.ayrshare.com
2. Connect your LinkedIn profile in the dashboard
3. Copy your API Key from Settings
4. Add to `.env`:
   ```
   AYRSHARE_API_KEY=your_key_here
   ```

**Usage:**
```bash
python run.py post --text "Your post"
python run.py post --schedule 2025-01-30T10:00:00 --text "Scheduled!"
python run.py post --pending  # Check scheduled posts
```

---

### Comparison

| Method | Cost | Free Tier | Scheduling | Token Expiry |
|--------|------|-----------|------------|--------------|
| **Zapier** | FREE | 100 tasks/mo | Via Zapier | Never |
| **Make.com** | FREE | 1000 ops/mo | Via Make | Never |
| **LinkedIn API** | FREE | Unlimited | ❌ Manual | 60 days |
| **Ayrshare** | $49/mo+ | ❌ None | ✅ Built-in | Never |

> **Note:** Buffer API was discontinued in 2019 and no longer accepts new apps.

---

## Complete Workflow Example

Here's a typical weekly workflow:

### Monday Morning - Generate Content

```bash
# 1. See what's trending on UAE subreddits
python run.py topics

# 2. Run full pipeline to generate posts
python run.py pipeline --count 5

# 3. Review generated posts
cat output/linkedin_posts.txt

# 4. Edit posts if needed (open in your editor)
code output/linkedin_posts.txt
```

### Throughout the Week - Post Content

```bash
# Post one immediately
python run.py post --file output/post1.txt

# Queue several for automatic posting
python run.py post --queue --file output/post2.txt
python run.py post --queue --file output/post3.txt

# Or schedule specific times
python run.py post --schedule 2025-01-30T09:00:00 --file output/post2.txt
python run.py post --schedule 2025-01-31T09:00:00 --file output/post3.txt
```

---

## Automated Full Workflow

For complete automation (scan → generate → post):

```bash
# Create this script: auto_pipeline.py
```

```python
#!/usr/bin/env python3
"""
Automated pipeline that:
1. Scans Reddit for relevant content
2. Generates LinkedIn posts
3. Queues them in Buffer for posting
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime

def run():
    project_dir = Path(__file__).parent

    # Run pipeline
    print("Running pipeline...")
    subprocess.run(
        ["python", "run.py", "pipeline", "--count", "3"],
        cwd=project_dir
    )

    # Read generated posts
    posts_file = project_dir / "output" / "linkedin_posts.txt"
    if not posts_file.exists():
        print("No posts generated")
        return

    content = posts_file.read_text()

    # Split into individual posts (separated by ---)
    posts = [p.strip() for p in content.split("---") if p.strip()]

    # Queue first post to Buffer
    if posts:
        print(f"Queueing {len(posts)} posts to Buffer...")
        for i, post in enumerate(posts[:3]):  # Max 3 posts
            # Save to temp file
            temp_file = project_dir / "output" / f"temp_post_{i}.txt"
            temp_file.write_text(post)

            # Queue to Buffer
            result = subprocess.run(
                ["python", "run.py", "post", "--queue", "--file", str(temp_file)],
                cwd=project_dir,
                capture_output=True,
                text=True
            )
            print(result.stdout)

            # Clean up
            temp_file.unlink()

    print("Done!")

if __name__ == "__main__":
    run()
```

Then schedule this script instead.

---

## Output Files

After running the pipeline, check the `output/` folder:

| File | Description |
|------|-------------|
| `pipeline_results.json` | Full data including Reddit posts, scores, comments |
| `linkedin_posts.txt` | Generated LinkedIn posts (ready to copy/paste) |
| `summary.md` | Human-readable summary report |
| `linkedin_posts_YYYY-MM-DD.md` | Date-stamped post archive |

---

## Environment Variables

```bash
# Required for AI generation
ANTHROPIC_API_KEY=sk-ant-...

# For posting (choose ONE - auto-detected, free options first)
ZAPIER_WEBHOOK_URL=...        # FREE - 100 tasks/mo
MAKE_WEBHOOK_URL=...          # FREE - 1000 ops/mo
LINKEDIN_ACCESS_TOKEN=...     # FREE but complex
AYRSHARE_API_KEY=...          # PAID - $49/mo+
```

---

## Troubleshooting

### "No relevant posts found"
- Reddit might be rate-limiting. Wait 5 minutes and try again.
- Try: `python run.py scan` to see what's available

### "ANTHROPIC_API_KEY not found"
- Make sure `.env` file exists with your API key
- Get one at https://console.anthropic.com/

### "No posting credentials found"
- Set up one of: Ayrshare, Zapier, Make, or LinkedIn API (see Posting section)

### Rate limit errors (429)
- Ayrshare free tier: 3 posts/day
- Add delays between posts if hitting limits

### Posts not appearing on LinkedIn
- Check your posting service dashboard (Ayrshare, Zapier, etc.)
- Verify your LinkedIn profile is connected

---

## Recommended Schedule

| Frequency | Best For |
|-----------|----------|
| Daily | High-volume content marketing |
| 2-3x/week | Active LinkedIn presence |
| Weekly | Sustainable content without burnout |

**Best posting times for UAE/Dubai audience:**
- Sunday-Thursday (UAE work week)
- 8-9 AM GST (morning commute)
- 12-1 PM GST (lunch break)
- 5-6 PM GST (end of workday)
