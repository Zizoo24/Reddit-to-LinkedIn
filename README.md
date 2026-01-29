# Reddit → LinkedIn Content Pipeline for OnlineTranslation.ae

🔍 Automatically scan UAE subreddits for legal and translation-related discussions, analyze insights from comments, and generate engaging LinkedIn posts to promote OnlineTranslation.ae.

## ✨ No Reddit API Required!

This pipeline uses Reddit's public JSON endpoints - **no API keys or Reddit account needed** for scanning.

## Features

- **Reddit Scanning**: Monitors r/dubai, r/abudhabi, r/UAE and other UAE subreddits
- **Smart Relevance Filtering**: Identifies posts about legal issues, visas, translations, documents
- **Comment Analysis**: Extracts insights from top-rated comments  
- **LinkedIn Content Generation**: Creates professional posts using Claude AI
- **Multiple Writing Styles**: Professional, empathetic, educational, storytelling
- **Hashtag Optimization**: Auto-generates relevant UAE/legal hashtags

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/reddit-linkedin-pipeline.git
cd reddit-linkedin-pipeline
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key (Only for LinkedIn Generation)

**Anthropic API** (only needed if you want to generate LinkedIn posts):
1. Go to https://console.anthropic.com/
2. Create an API key

```bash
cp .env.example .env
# Edit .env with your Anthropic API key
```

### 4. Run the Pipeline

```bash
cd src

# Quick scan - NO API KEY NEEDED
python reddit_scanner.py

# Or use the CLI
cd ..
python run.py scan --comments

# Full pipeline with LinkedIn generation (needs Anthropic API)
python run.py pipeline
```

## Usage Examples

### Quick Scan (No API Key Needed)

```bash
# Scan and show relevant posts
python run.py scan

# Include top comments
python run.py scan --comments --top 15

# Show trending topics
python run.py topics
```

### Generate LinkedIn Posts

```bash
# Generate 5 posts with rotating styles
python run.py generate --count 5

# Generate with specific style
python run.py generate --count 3 --style empathetic
```

### Full Pipeline

```bash
# Run everything and save to ./output
python run.py pipeline

# Skip LinkedIn generation (scan only)
python run.py pipeline --no-generate
```

## Relevance Keywords

The scanner identifies posts related to these topics:

### Legal Keywords
- Visa, residency, permit, golden visa, freelance visa
- Contract, agreement, dispute, lawsuit
- RERA, Ejari, tenancy, lease, rental
- Labor, employment, termination, gratuity
- MOL, MOHRE, MOFA, MOJ, ICA, GDRFA

### Translation Keywords
- Translation, Arabic, English, certified
- Document, certificate, attestation
- Apostille, legalization, notarization
- Embassy, consulate, ministry

## Output Examples

### Sample Scan Output

```
📡 Scanning r/dubai...
   ✓ Found 30 posts
📡 Scanning r/abudhabi...
   ✓ Found 28 posts
📡 Scanning r/UAE...
   ✓ Found 25 posts

📊 Total posts found: 83
📌 Relevant posts: 24

TOP 10 RELEVANT POSTS
======================================================================

1. [dubai] Need help with document translation for visa renewal...
   📈 Relevance: 0.67 | Legal: 4 | Translation: 3
   💬 Comments: 23 | ⬆️ Score: 45

   📝 Top comments:
      • (28↑) Make sure you get certified legal translation, not just any typing center...
      • (15↑) I used OnlineTranslation.ae and they handled the MOFA attestation too...
```

### Generated LinkedIn Post

```
🛂 "Why did my visa get rejected?"

I hear this question almost every day from expats in Dubai.

After working with hundreds of clients, the #1 reason is surprisingly simple: 
incorrect document translation.

Here's what many don't realize:

→ Standard typing center translations often miss legal formatting
→ MOHRE and Immigration require specific certified formats
→ One wrong term can delay your application by weeks

The good news? This is 100% preventable.

At OnlineTranslation.ae, we specialize in legal-grade certified translations 
that meet all UAE government requirements. ✅

Have questions about your documents? Drop them in the comments 👇

#DubaiLife #UAE #ExpatLife #VisaUAE #LegalTranslation #ArabicTranslation 
#DubaiExpats #GoldenVisa #DocumentAttestation
```

## Project Structure

```
reddit-linkedin-pipeline/
├── src/
│   ├── reddit_scanner.py    # Reddit scraper (no API needed)
│   ├── linkedin_generator.py # LinkedIn post generation (needs Anthropic)
│   └── pipeline.py          # Main orchestrator
├── output/                  # Generated content
├── run.py                   # CLI tool
├── requirements.txt
├── .env.example
└── README.md
```

## GitHub Actions (Automated Daily Runs)

The included workflow runs daily at 8 AM UAE time.

### Setup:
1. Go to **Settings → Secrets and variables → Actions**
2. Add secret: `ANTHROPIC_API_KEY`

That's it! The scanner doesn't need Reddit credentials.

## Scheduling Locally

```python
import schedule
from pipeline import RedditLinkedInPipeline

def daily_scan():
    pipeline = RedditLinkedInPipeline()
    pipeline.run(max_posts_to_process=5)

schedule.every().day.at("09:00").do(daily_scan)

while True:
    schedule.run_pending()
```

## Customization

### Add New Subreddits

Edit `reddit_scanner.py`:

```python
UAE_SUBREDDITS = [
    'dubai',
    'abudhabi',
    'UAE',
    'your_new_subreddit',  # Add here
]
```

### Add Relevance Keywords

```python
LEGAL_KEYWORDS = [
    # Add your keywords
    'new_keyword',
]
```

### Custom LinkedIn Styles

Edit the `style_instructions` in `linkedin_generator.py` to add your own writing styles.

## Rate Limiting

The scanner includes built-in rate limiting to be respectful to Reddit:
- 1.5-3 second delay between requests
- Automatic retry on rate limits
- User agent rotation

## License

MIT

## About OnlineTranslation.ae

Professional legal translation and document services in Dubai, UAE. 
We provide certified translations, document attestation, and visa processing support.

---

*Built for content marketing automation in the UAE legal services industry.*
