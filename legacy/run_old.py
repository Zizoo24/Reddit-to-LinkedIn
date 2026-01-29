#!/usr/bin/env python3
"""
CLI Runner for Reddit to LinkedIn Pipeline
Usage: python run.py [command] [options]
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from reddit_scanner import RedditScanner
from linkedin_generator import LinkedInPostGenerator
from pipeline import RedditLinkedInPipeline
from linkedin_poster import get_poster


def cmd_scan(args):
    """Quick scan command - find relevant posts without generating content"""
    load_dotenv()
    
    scanner = RedditScanner()
    
    print(f"\n🔍 Scanning UAE subreddits (limit: {args.limit} per sub)...\n")
    
    posts = scanner.scan_all_uae_subreddits(limit_per_sub=args.limit)
    sorted_posts = scanner.sort_posts(posts, 'relevance_date')
    relevant = scanner.filter_by_relevance(sorted_posts, min_score=args.min_relevance)
    
    print(f"\n✓ Found {len(relevant)} relevant posts\n")
    print("="*70)
    
    for i, post in enumerate(relevant[:args.top], 1):
        print(f"\n{i}. [{post['subreddit']}] {post['title']}")
        print(f"   Relevance: {post['relevance']['combined']:.2f} | "
              f"Legal: {post['relevance']['legal_matches']} | "
              f"Translation: {post['relevance']['translation_matches']}")
        print(f"   Score: {post['score']} | Comments: {post['num_comments']}")
        print(f"   URL: {post['url']}")
        
        if args.comments:
            comments = scanner.get_post_comments(post['id'], limit=2)
            if comments:
                print("\n   📝 Top comment:")
                preview = comments[0]['body'][:200].replace('\n', ' ')
                print(f"   \"{preview}...\"")


def cmd_generate(args):
    """Generate LinkedIn posts from top Reddit content"""
    load_dotenv()
    
    scanner = RedditScanner()
    generator = LinkedInPostGenerator()
    
    print(f"\n🔍 Scanning for content...\n")
    
    posts = scanner.scan_all_uae_subreddits(limit_per_sub=args.limit)
    sorted_posts = scanner.sort_posts(posts, 'relevance_date')
    relevant = scanner.filter_by_relevance(sorted_posts, min_score=0.2)
    
    if not relevant:
        print("No relevant posts found. Try lowering --min-relevance")
        return
    
    top_posts = relevant[:args.count]
    
    print(f"✓ Found {len(relevant)} relevant posts, generating from top {len(top_posts)}\n")
    
    styles = ['professional', 'empathetic', 'educational', 'storytelling']
    
    for i, post in enumerate(top_posts):
        style = args.style if args.style else styles[i % len(styles)]
        
        print(f"\n{'='*70}")
        print(f"Generating post {i+1}/{len(top_posts)} ({style})")
        print(f"Source: {post['title'][:60]}...")
        print("="*70)
        
        comments = scanner.get_post_comments(post['id'], limit=5)
        
        try:
            linkedin_post = generator.generate_post(
                reddit_post=post,
                comments=comments,
                style=style
            )
            
            print(f"\n{linkedin_post['content']}")
            print(f"\n📎 Source: {post['url']}")
        except Exception as e:
            print(f"Error generating: {e}")


def cmd_pipeline(args):
    """Run the full pipeline"""
    load_dotenv()
    
    pipeline = RedditLinkedInPipeline(output_dir=args.output)
    
    print("\n🚀 Running full pipeline...\n")
    
    results = pipeline.run(
        posts_per_subreddit=args.limit,
        min_relevance=args.min_relevance,
        max_posts_to_process=args.count,
        comments_per_post=5,
        generate_posts=not args.no_generate
    )
    
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE!")
    print("="*70)
    print(f"\nOutput saved to: {args.output}/")


def cmd_topics(args):
    """Show trending topics in UAE subreddits"""
    load_dotenv()

    scanner = RedditScanner()

    print("\n📊 Analyzing trending topics in UAE subreddits...\n")

    posts = scanner.scan_all_uae_subreddits(limit_per_sub=50)

    # Count topic occurrences
    from collections import Counter
    from reddit_scanner import LEGAL_KEYWORDS, TRANSLATION_KEYWORDS

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

    print("🏛️  TOP LEGAL TOPICS:")
    for topic, count in legal_counts.most_common(15):
        print(f"   {topic}: {count} mentions")

    print("\n📄 TOP TRANSLATION TOPICS:")
    for topic, count in translation_counts.most_common(10):
        print(f"   {topic}: {count} mentions")

    # Subreddit breakdown
    from collections import defaultdict
    sub_counts = defaultdict(int)
    for post in posts:
        if post['relevance']['combined'] > 0.1:
            sub_counts[post['subreddit']] += 1

    print("\n📍 RELEVANT POSTS BY SUBREDDIT:")
    for sub, count in sorted(sub_counts.items(), key=lambda x: -x[1]):
        print(f"   r/{sub}: {count} posts")


def cmd_post(args):
    """Post to LinkedIn via Buffer or LinkedIn API"""
    load_dotenv()

    try:
        poster = get_poster(args.method)
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nSetup required (FREE options):")
        print("  Option 1 - Zapier (FREE - 100 tasks/month):")
        print("    1. Create Zap at https://zapier.com: Webhook → LinkedIn")
        print("    2. Add ZAPIER_WEBHOOK_URL to your .env file")
        print("\n  Option 2 - Make.com (FREE - 1000 ops/month):")
        print("    1. Create scenario at https://make.com: Webhook → LinkedIn")
        print("    2. Add MAKE_WEBHOOK_URL to your .env file")
        print("\n  Option 3 - LinkedIn Direct API (FREE but complex):")
        print("    1. Create app at https://www.linkedin.com/developers/apps")
        print("    2. Add LINKEDIN_ACCESS_TOKEN to your .env file")
        return

    if args.list_profiles:
        print("\n📋 Connected profiles:\n")
        profiles = poster.get_profiles()
        for p in profiles:
            marker = "→" if p.get('service') == 'linkedin' else " "
            print(f"  {marker} {p.get('service')}: {p.get('formatted_username')} (ID: {p.get('id')})")
        return

    if args.pending:
        print("\n⏳ Pending posts:\n")
        pending = poster.get_pending_posts()
        if not pending:
            print("  No pending posts")
        for post in pending:
            preview = post.get('text', '')[:80].replace('\n', ' ')
            print(f"  • {preview}...")
        return

    # Get text to post
    text = args.text
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()

    if not text:
        print("❌ Provide --text or --file with content to post")
        return

    # Post or queue
    from datetime import datetime

    if args.queue:
        result = poster.add_to_queue(text)
        print("\n✅ Added to queue!")
        print("   Will be posted at next scheduled time")
    elif args.schedule:
        scheduled_at = datetime.fromisoformat(args.schedule)
        result = poster.schedule_post(text, scheduled_at)
        print(f"\n✅ Scheduled for {scheduled_at}")
    else:
        result = poster.post_now(text)
        print("\n✅ Posted to LinkedIn!")

    if args.verbose:
        import json
        print(f"\nAPI Response:\n{json.dumps(result, indent=2)}")


def main():
    parser = argparse.ArgumentParser(
        description='Reddit to LinkedIn Pipeline for OnlineTranslation.ae',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py scan                    # Quick scan for relevant posts
  python run.py scan --comments         # Include top comments in output
  python run.py generate --count 3      # Generate 3 LinkedIn posts
  python run.py generate --style empathetic
  python run.py pipeline                # Run full pipeline
  python run.py topics                  # Show trending topics

  # LinkedIn posting (requires Ayrshare, Zapier, or Make setup)
  python run.py post --list-profiles    # List connected profiles
  python run.py post --text "Hello!"    # Post immediately (auto-detects method)
  python run.py post --file post.txt    # Post from file
  python run.py post --method zapier --text "Via Zapier"  # Use specific method
  python run.py post --schedule 2025-01-30T10:00:00 --text "Scheduled!"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Quick scan for relevant posts')
    scan_parser.add_argument('--limit', type=int, default=30, help='Posts per subreddit')
    scan_parser.add_argument('--top', type=int, default=10, help='Show top N results')
    scan_parser.add_argument('--min-relevance', type=float, default=0.15, help='Minimum relevance score')
    scan_parser.add_argument('--comments', action='store_true', help='Include top comments')
    scan_parser.set_defaults(func=cmd_scan)
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate LinkedIn posts')
    gen_parser.add_argument('--count', type=int, default=3, help='Number of posts to generate')
    gen_parser.add_argument('--limit', type=int, default=30, help='Posts per subreddit to scan')
    gen_parser.add_argument('--style', choices=['professional', 'empathetic', 'educational', 'storytelling'],
                          help='Writing style (default: rotate through all)')
    gen_parser.set_defaults(func=cmd_generate)
    
    # Pipeline command
    pipe_parser = subparsers.add_parser('pipeline', help='Run full pipeline')
    pipe_parser.add_argument('--limit', type=int, default=30, help='Posts per subreddit')
    pipe_parser.add_argument('--count', type=int, default=10, help='Max posts to process')
    pipe_parser.add_argument('--min-relevance', type=float, default=0.15, help='Minimum relevance score')
    pipe_parser.add_argument('--output', type=str, default='./output', help='Output directory')
    pipe_parser.add_argument('--no-generate', action='store_true', help='Skip LinkedIn generation')
    pipe_parser.set_defaults(func=cmd_pipeline)
    
    # Topics command
    topics_parser = subparsers.add_parser('topics', help='Show trending topics')
    topics_parser.set_defaults(func=cmd_topics)

    # Post command
    post_parser = subparsers.add_parser('post', help='Post to LinkedIn')
    post_parser.add_argument('--method', choices=['ayrshare', 'zapier', 'make', 'linkedin', 'auto'], default='auto',
                            help='Posting method (default: auto-detect from env)')
    post_parser.add_argument('--text', help='Text to post')
    post_parser.add_argument('--file', help='File containing post text')
    post_parser.add_argument('--list-profiles', action='store_true', help='List connected profiles')
    post_parser.add_argument('--pending', action='store_true', help='Show pending posts')
    post_parser.add_argument('--queue', action='store_true', help='Add to Buffer queue')
    post_parser.add_argument('--schedule', help='Schedule post (ISO format: 2025-01-30T10:00:00)')
    post_parser.add_argument('--verbose', '-v', action='store_true', help='Show API response')
    post_parser.set_defaults(func=cmd_post)

    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
