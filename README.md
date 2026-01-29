# Reddit-to-LinkedIn Content Generator

Generate LinkedIn posts for **OnlineTranslation.ae** by scanning Reddit and other sources for relevant UAE expat discussions.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Add your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Generate 5 posts
python generate.py
```

## What It Does

1. **Scans** UAE subreddits (r/dubai, r/abudhabi, r/UAE, etc.) for recent discussions
2. **Identifies** posts about visas, documents, translation, legal issues, and trending topics
3. **Generates** 5 LinkedIn posts using Claude AI
4. **Saves** posts and source data to `output/` folder

## Commands

```bash
python generate.py              # Generate 5 posts
python generate.py --scan-only  # Just scan Reddit, no generation
python generate.py --topics     # Show trending topics analysis
```

## Output

Each run creates two files in `output/`:
- `posts_YYYY-MM-DD_HHMM.md` - The generated LinkedIn posts
- `sources_YYYY-MM-DD_HHMM.json` - Source data that inspired the posts

## Content Strategy

See `output/PROMPT.md` for the full content strategy guide including:
- Tone and voice guidelines
- Post templates
- Hashtag recommendations
- Quality checklist

## Requirements

- Python 3.8+
- Anthropic API key (for Claude)
- No Reddit API key needed (uses public JSON endpoints)

## Folder Structure

```
├── generate.py          # Main script - run this
├── output/
│   ├── PROMPT.md        # Content strategy & templates
│   └── posts_*.md       # Generated posts
├── src/
│   └── reddit_scanner.py # Reddit scraping logic
└── legacy/              # Old automation code (archived)
```

## License

MIT
