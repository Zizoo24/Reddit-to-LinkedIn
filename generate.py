#!/usr/bin/env python3
"""
Simple LinkedIn Post Generator for OnlineTranslation.ae

Scans multiple sources and generates 5 LinkedIn posts.
No automation, no scheduling - just run and get posts.

Usage:
    python generate.py              # Generate 5 posts
    python generate.py --scan-only  # Just scan, no generation
    python generate.py --topics     # Show trending topics
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from reddit_scanner import RedditScanner, LEGAL_KEYWORDS, TRANSLATION_KEYWORDS


def scan_reddit():
    """Scan Reddit for relevant content."""
    print("\n" + "="*60)
    print("📡 SCANNING REDDIT")
    print("="*60)

    scanner = RedditScanner()
    posts = scanner.scan_all_uae_subreddits(limit_per_sub=30)

    # Sort by relevance + recency
    sorted_posts = scanner.sort_posts(posts, 'relevance_date')

    # Get top relevant posts
    relevant = scanner.filter_by_relevance(sorted_posts, min_score=0.1)

    print(f"\n✓ Found {len(posts)} total posts")
    print(f"✓ {len(relevant)} posts with relevance score >= 0.1")

    return relevant, scanner


def get_trending_topics(posts):
    """Analyze trending topics from posts."""
    from collections import Counter

    legal_counts = Counter()
    translation_counts = Counter()

    for post in posts:
        text = f"{post['title']} {post['selftext']}".lower()
        for kw in LEGAL_KEYWORDS:
            if kw in text:
                legal_counts[kw] += 1
        for kw in TRANSLATION_KEYWORDS:
            if kw in text:
                translation_counts[kw] += 1

    return legal_counts, translation_counts


def display_scan_results(posts, scanner):
    """Display scan results."""
    print("\n" + "="*60)
    print("📊 TOP RELEVANT POSTS")
    print("="*60)

    for i, post in enumerate(posts[:10], 1):
        print(f"\n{i}. [{post['subreddit']}] {post['title'][:60]}...")
        print(f"   Relevance: {post['relevance']['combined']:.2f} | "
              f"Legal: {post['relevance']['legal_matches']} | "
              f"Translation: {post['relevance']['translation_matches']}")
        print(f"   Score: {post['score']} | Comments: {post['num_comments']}")
        print(f"   URL: {post['url']}")


def generate_posts(posts, scanner):
    """Generate 5 LinkedIn posts using Claude."""
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n❌ ANTHROPIC_API_KEY not found in .env")
        print("   Get one at https://console.anthropic.com/")
        return None

    try:
        import anthropic
    except ImportError:
        print("\n❌ anthropic package not installed")
        print("   Run: pip install anthropic")
        return None

    print("\n" + "="*60)
    print("🤖 GENERATING LINKEDIN POSTS")
    print("="*60)

    # Read the prompt template
    prompt_file = Path(__file__).parent / "output" / "PROMPT.md"
    if prompt_file.exists():
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    else:
        prompt_template = "You are a content marketing assistant for OnlineTranslation.ae, a legal translation company in Dubai."

    # Prepare source material from top posts
    source_material = []
    for i, post in enumerate(posts[:15], 1):
        # Get comments for top 5 posts
        comments_text = ""
        if i <= 5 and post['num_comments'] > 0:
            comments = scanner.get_post_comments(post['subreddit'], post['id'], limit=5)
            if comments:
                top_comments = [c['body'][:300] for c in comments[:3]]
                comments_text = "\nTop comments:\n- " + "\n- ".join(top_comments)

        source_material.append(f"""
### Source {i}: r/{post['subreddit']}
**Title:** {post['title']}
**Content:** {post['selftext'][:500] if post['selftext'] else '[Link post]'}
**Engagement:** {post['score']} upvotes, {post['num_comments']} comments
**URL:** {post['url']}
{comments_text}
""")

    # Build the generation prompt
    generation_prompt = f"""
{prompt_template}

---

## TODAY'S SOURCE MATERIAL

The following are recent posts from UAE subreddits. Use these as inspiration for generating 5 LinkedIn posts.

{"".join(source_material)}

---

## YOUR TASK

Generate exactly 5 LinkedIn posts for OnlineTranslation.ae based on the source material above.

Requirements:
1. Each post should use a DIFFERENT template/approach from the PROMPT.md
2. Mix of direct relevance (visa, documents, translation) and tangential topics
3. At least ONE post should be about something trending/viral if you can find it
4. Each post should be 150-300 words
5. Include 8-12 hashtags per post
6. End each post with an engagement question

Format each post as:

## Post [N]: [Topic Title]

**Source:** [Which source inspired this]
**Template:** [Template name from PROMPT.md]
**Relevance:** [Direct/Tangential/Trending]

---

[THE ACTUAL LINKEDIN POST HERE]

---

Generate all 5 posts now.
"""

    # Call Claude
    client = anthropic.Anthropic(api_key=api_key)

    print("\n🔄 Calling Claude API...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[
            {"role": "user", "content": generation_prompt}
        ]
    )

    generated_content = response.content[0].text

    print("✓ Generated 5 posts")

    return generated_content


def save_output(content, posts):
    """Save output to files."""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")

    # Save posts
    posts_file = output_dir / f"posts_{timestamp}.md"
    with open(posts_file, 'w', encoding='utf-8') as f:
        f.write(f"# LinkedIn Posts Generated {timestamp}\n\n")
        f.write(content)

    print(f"\n✓ Saved posts to: {posts_file}")

    # Save source data
    sources_file = output_dir / f"sources_{timestamp}.json"

    # Convert datetime objects to strings for JSON
    posts_data = []
    for p in posts[:15]:
        post_copy = p.copy()
        post_copy['created_utc'] = post_copy['created_utc'].isoformat()
        posts_data.append(post_copy)

    with open(sources_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generated_at": timestamp,
            "sources": posts_data
        }, f, indent=2)

    print(f"✓ Saved sources to: {sources_file}")

    return posts_file


def main():
    parser = argparse.ArgumentParser(
        description='Generate LinkedIn posts for OnlineTranslation.ae',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py              # Generate 5 posts
  python generate.py --scan-only  # Just scan sources
  python generate.py --topics     # Show trending topics
        """
    )
    parser.add_argument('--scan-only', action='store_true',
                        help='Only scan, do not generate posts')
    parser.add_argument('--topics', action='store_true',
                        help='Show trending topics analysis')

    args = parser.parse_args()

    # Scan Reddit
    posts, scanner = scan_reddit()

    if not posts:
        print("\n❌ No posts found. Reddit may be rate-limiting.")
        return

    # Show trending topics
    if args.topics:
        legal_counts, translation_counts = get_trending_topics(posts)

        print("\n" + "="*60)
        print("📈 TRENDING TOPICS")
        print("="*60)

        print("\n🏛️ Legal Topics:")
        for topic, count in legal_counts.most_common(15):
            print(f"   {topic}: {count}")

        print("\n📄 Translation Topics:")
        for topic, count in translation_counts.most_common(10):
            print(f"   {topic}: {count}")
        return

    # Display results
    display_scan_results(posts, scanner)

    if args.scan_only:
        return

    # Generate posts
    content = generate_posts(posts, scanner)

    if content:
        # Save output
        output_file = save_output(content, posts)

        # Display generated content
        print("\n" + "="*60)
        print("📝 GENERATED POSTS")
        print("="*60)
        print(content)

        print("\n" + "="*60)
        print("✅ DONE")
        print("="*60)
        print(f"\nPosts saved to: {output_file}")
        print("\nNext steps:")
        print("  1. Review and edit the posts")
        print("  2. Copy to LinkedIn")
        print("  3. Schedule or post manually")


if __name__ == '__main__':
    main()
