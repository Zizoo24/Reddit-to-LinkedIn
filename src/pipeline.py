"""
Reddit to LinkedIn Pipeline
Main orchestrator for scanning Reddit and generating LinkedIn content
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from reddit_scanner import RedditScanner, UAE_SUBREDDITS
from linkedin_generator import LinkedInPostGenerator


class RedditLinkedInPipeline:
    def __init__(self, output_dir: str = None, use_demo: bool = False):
        """Initialize the pipeline
        
        Args:
            output_dir: Directory to save output files
            use_demo: If True, use demo data instead of live Reddit
        """
        self.use_demo = use_demo
        self.scanner = RedditScanner()
        self.generator = LinkedInPostGenerator()
        self.output_dir = Path(output_dir or './output')
        self.output_dir.mkdir(exist_ok=True)
        
        # Check Reddit access if not using demo
        if not use_demo:
            try:
                test_posts = self.scanner.scan_subreddit('dubai', limit=1, sort='hot')
                if not test_posts:
                    print("⚠️  Reddit access blocked. Switching to demo mode.")
                    print("   (This is normal for cloud/server environments)")
                    self.use_demo = True
            except Exception as e:
                print(f"⚠️  Reddit access error: {e}")
                print("   Switching to demo mode.")
                self.use_demo = True
    
    def run(self, 
            posts_per_subreddit: int = 30,
            min_relevance: float = 0.15,
            max_posts_to_process: int = 10,
            comments_per_post: int = 5,
            generate_posts: bool = True) -> Dict:
        """
        Run the full pipeline
        
        Args:
            posts_per_subreddit: Number of posts to scan per subreddit
            min_relevance: Minimum relevance score to include
            max_posts_to_process: Maximum posts to generate LinkedIn content for
            comments_per_post: Number of top comments to analyze per post
            generate_posts: Whether to generate LinkedIn posts (requires API key)
        
        Returns:
            Pipeline results dictionary
        """
        results = {
            'run_timestamp': datetime.now().isoformat(),
            'config': {
                'posts_per_subreddit': posts_per_subreddit,
                'min_relevance': min_relevance,
                'max_posts': max_posts_to_process
            },
            'stats': {},
            'posts': [],
            'linkedin_posts': []
        }
        
        # Step 1: Scan Reddit (or use demo data)
        print("\n" + "="*60)
        if self.use_demo:
            print("STEP 1: LOADING DEMO DATA")
            print("="*60)
            print("(Using demo data - Reddit blocked from this environment)")
            from reddit_scanner_websearch import get_demo_data, DEMO_COMMENTS
            all_posts, _ = get_demo_data()
        else:
            print("STEP 1: SCANNING UAE SUBREDDITS")
            print("="*60)
            all_posts = self.scanner.scan_all_uae_subreddits(
                limit_per_sub=posts_per_subreddit
            )
        results['stats']['total_scanned'] = len(all_posts)
        print(f"\n✓ {'Loaded' if self.use_demo else 'Scanned'} {len(all_posts)} total posts")
        
        # Step 2: Sort and Filter
        print("\n" + "="*60)
        print("STEP 2: SORTING & FILTERING BY RELEVANCE")
        print("="*60)
        
        sorted_posts = self.scanner.sort_posts(all_posts, 'relevance_date')
        relevant_posts = self.scanner.filter_by_relevance(
            sorted_posts, 
            min_score=min_relevance
        )
        results['stats']['relevant_posts'] = len(relevant_posts)
        print(f"\n✓ Found {len(relevant_posts)} relevant posts")
        
        # Step 3: Get Comments
        print("\n" + "="*60)
        print("STEP 3: ANALYZING COMMENTS FOR INSIGHTS")
        print("="*60)
        
        posts_to_process = relevant_posts[:max_posts_to_process]
        posts_with_comments = []
        
        # Load demo comments if in demo mode
        demo_comments = {}
        if self.use_demo:
            from reddit_scanner_websearch import DEMO_COMMENTS
            demo_comments = DEMO_COMMENTS
        
        for i, post in enumerate(posts_to_process, 1):
            print(f"\n[{i}/{len(posts_to_process)}] {post['title'][:50]}...")
            
            try:
                if self.use_demo:
                    # Use demo comments
                    comments = demo_comments.get(post['id'], [])
                else:
                    comments = self.scanner.get_post_comments(
                        post['subreddit'],
                        post['id'], 
                        limit=comments_per_post
                    )
                posts_with_comments.append({
                    'post': post,
                    'comments': comments,
                    'insights': self._extract_insights(comments)
                })
                print(f"  ✓ Got {len(comments)} comments")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                posts_with_comments.append({
                    'post': post,
                    'comments': [],
                    'insights': []
                })
        
        results['posts'] = posts_with_comments
        
        # Step 4: Generate LinkedIn Posts
        if generate_posts:
            print("\n" + "="*60)
            print("STEP 4: GENERATING LINKEDIN POSTS")
            print("="*60)
            
            linkedin_posts = self.generator.generate_batch(posts_with_comments)
            results['linkedin_posts'] = linkedin_posts
            results['stats']['posts_generated'] = len(linkedin_posts)
            print(f"\n✓ Generated {len(linkedin_posts)} LinkedIn posts")
        
        # Step 5: Save Results
        print("\n" + "="*60)
        print("STEP 5: SAVING RESULTS")
        print("="*60)
        
        self._save_results(results)
        
        return results
    
    def _extract_insights(self, comments: List[Dict]) -> List[str]:
        """Extract key insights from comments"""
        insights = []
        
        for comment in comments:
            if comment['score'] >= 5:  # Only from well-received comments
                body = comment['body']
                
                # Look for actionable advice patterns
                if any(phrase in body.lower() for phrase in [
                    'make sure', 'don\'t forget', 'important', 'tip:',
                    'pro tip', 'advice', 'recommend', 'should', 'must'
                ]):
                    # Extract first sentence or first 200 chars
                    insight = body.split('.')[0][:200]
                    insights.append(insight)
        
        return insights[:3]  # Top 3 insights
    
    def _save_results(self, results: Dict):
        """Save pipeline results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save full JSON results
        json_path = self.output_dir / f'pipeline_results_{timestamp}.json'
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"✓ Saved JSON results to {json_path}")
        
        # Save LinkedIn posts as formatted text
        if results.get('linkedin_posts'):
            posts_path = self.output_dir / f'linkedin_posts_{timestamp}.txt'
            formatted = self.generator.format_for_review(results['linkedin_posts'])
            with open(posts_path, 'w') as f:
                f.write(formatted)
            print(f"✓ Saved LinkedIn posts to {posts_path}")
        
        # Save summary report
        report_path = self.output_dir / f'summary_{timestamp}.md'
        report = self._generate_report(results)
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"✓ Saved summary report to {report_path}")
    
    def _generate_report(self, results: Dict) -> str:
        """Generate a markdown summary report"""
        stats = results.get('stats', {})
        
        report = f"""# Reddit → LinkedIn Pipeline Report

**Run Time:** {results['run_timestamp']}

## Statistics

| Metric | Value |
|--------|-------|
| Posts Scanned | {stats.get('total_scanned', 'N/A')} |
| Relevant Posts | {stats.get('relevant_posts', 'N/A')} |
| LinkedIn Posts Generated | {stats.get('posts_generated', 'N/A')} |

## Top Reddit Posts Analyzed

"""
        
        for i, item in enumerate(results.get('posts', [])[:5], 1):
            post = item['post']
            report += f"""### {i}. {post['title'][:70]}...

- **Subreddit:** r/{post['subreddit']}
- **Engagement:** {post['score']} upvotes, {post['num_comments']} comments
- **Relevance Score:** {post['relevance']['combined']:.2f}
- **URL:** {post['url']}

"""
            if item.get('insights'):
                report += "**Key Insights from Comments:**\n"
                for insight in item['insights']:
                    report += f"- {insight}\n"
            report += "\n---\n\n"
        
        if results.get('linkedin_posts'):
            report += "\n## Generated LinkedIn Posts\n\n"
            report += f"Generated {len(results['linkedin_posts'])} posts ready for review.\n"
            report += "See `linkedin_posts_*.txt` for full content.\n"
        
        return report


def run_quick_scan():
    """Quick scan without generating LinkedIn posts (no API key needed)"""
    pipeline = RedditLinkedInPipeline()
    
    print("\n🔍 Running quick scan (no LinkedIn generation)...\n")
    
    results = pipeline.run(
        posts_per_subreddit=20,
        min_relevance=0.1,
        max_posts_to_process=5,
        generate_posts=False
    )
    
    print("\n" + "="*60)
    print("QUICK SCAN RESULTS")
    print("="*60)
    
    for i, item in enumerate(results['posts'][:5], 1):
        post = item['post']
        print(f"\n{i}. [{post['subreddit']}] {post['title'][:60]}...")
        print(f"   Relevance: {post['relevance']['combined']:.2f} | "
              f"Comments: {post['num_comments']} | Score: {post['score']}")
        
        if item['comments']:
            print("   Top comment preview:")
            preview = item['comments'][0]['body'][:100].replace('\n', ' ')
            print(f"   \"{preview}...\"")


def run_full_pipeline():
    """Run full pipeline with LinkedIn post generation"""
    pipeline = RedditLinkedInPipeline()
    
    print("\n🚀 Running full pipeline...\n")
    
    results = pipeline.run(
        posts_per_subreddit=30,
        min_relevance=0.15,
        max_posts_to_process=10,
        comments_per_post=5,
        generate_posts=True
    )
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE!")
    print("="*60)
    print(f"\nCheck the ./output directory for:")
    print("  - pipeline_results_*.json (full data)")
    print("  - linkedin_posts_*.txt (ready-to-post content)")
    print("  - summary_*.md (overview report)")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        run_quick_scan()
    else:
        run_full_pipeline()
