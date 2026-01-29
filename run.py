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
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
