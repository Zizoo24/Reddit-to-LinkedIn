"""
Reddit Scanner for UAE Subreddits (No API Required)
Uses Reddit's public JSON endpoints to scrape posts and comments
"""

import requests
import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Keywords for relevance scoring
LEGAL_KEYWORDS = [
    'legal', 'lawyer', 'attorney', 'court', 'visa', 'residency', 'permit',
    'contract', 'agreement', 'dispute', 'lawsuit', 'litigation', 'notary',
    'attestation', 'legalization', 'power of attorney', 'poa', 'will',
    'inheritance', 'divorce', 'custody', 'labor', 'employment', 'termination',
    'gratuity', 'rera', 'ejari', 'tenancy', 'lease', 'rental', 'landlord',
    'tenant', 'eviction', 'deposit', 'cheque', 'bounce', 'debt', 'fine',
    'traffic', 'violation', 'immigration', 'deportation', 'ban', 'overstay',
    'sponsor', 'sponsorship', 'golden visa', 'freelance visa', 'company setup',
    'trade license', 'freezone', 'mainland', 'llc', 'establishment card',
    'mol', 'mohre', 'mofa', 'moj', 'ica', 'gdrfa', 'dha', 'dewa',
    'typing center', 'amer', 'tasheel', 'tas-heel'
]

TRANSLATION_KEYWORDS = [
    'translation', 'translate', 'translator', 'arabic', 'english',
    'document', 'certificate', 'degree', 'diploma', 'transcript',
    'birth certificate', 'marriage certificate', 'death certificate',
    'police clearance', 'good conduct', 'medical report', 'attestation',
    'apostille', 'legalization', 'notarization', 'certified', 'sworn',
    'official', 'embassy', 'consulate', 'ministry', 'government'
]

UAE_SUBREDDITS = [
    'dubai',
    'abudhabi', 
    'UAE',
    'DubaiPetrolHeads',
    'dubaijobs'
]

# User agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]


class RedditScanner:
    """Scrape Reddit using public JSON endpoints - no API key required"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.reddit.com"
        self._update_headers()
    
    def _update_headers(self):
        """Set headers that work with Reddit's API"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """Make request with retry logic and rate limiting"""
        for attempt in range(max_retries):
            try:
                # Rate limiting - be nice to Reddit
                time.sleep(random.uniform(1.5, 3.0))
                
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = (attempt + 1) * 10
                    print(f"  Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    self._update_headers()
                elif response.status_code == 403:
                    print(f"  Access forbidden, rotating user agent...")
                    self._update_headers()
                    time.sleep(5)
                else:
                    print(f"  HTTP {response.status_code}, retrying...")
                    time.sleep(3)
                    
            except requests.exceptions.RequestException as e:
                print(f"  Request error: {e}")
                time.sleep(3)
        
        return None
    
    def calculate_relevance_score(self, text: str) -> Dict[str, float]:
        """Calculate relevance scores for legal and translation topics"""
        text_lower = text.lower()
        
        legal_score = sum(1 for kw in LEGAL_KEYWORDS if kw in text_lower)
        translation_score = sum(1 for kw in TRANSLATION_KEYWORDS if kw in text_lower)
        
        return {
            'legal': min(legal_score / 5, 1.0),
            'translation': min(translation_score / 3, 1.0),
            'combined': min((legal_score + translation_score) / 6, 1.0),
            'legal_matches': legal_score,
            'translation_matches': translation_score
        }
    
    def scan_subreddit(self, subreddit_name: str, limit: int = 50, 
                       sort: str = 'new') -> List[Dict]:
        """Scan a subreddit for posts using JSON endpoint"""
        posts = []
        after = None
        fetched = 0
        
        while fetched < limit:
            # Build URL
            url = f"{self.base_url}/r/{subreddit_name}/{sort}.json?limit=25"
            if after:
                url += f"&after={after}"
            
            data = self._make_request(url)
            
            if not data or 'data' not in data:
                break
            
            children = data['data'].get('children', [])
            if not children:
                break
            
            for child in children:
                post_data = child.get('data', {})
                processed = self._process_post(post_data, subreddit_name)
                if processed:
                    posts.append(processed)
                    fetched += 1
                    
                    if fetched >= limit:
                        break
            
            # Get next page token
            after = data['data'].get('after')
            if not after:
                break
        
        return posts
    
    def _process_post(self, post_data: Dict, subreddit_name: str) -> Optional[Dict]:
        """Process raw post data from JSON"""
        title = post_data.get('title', '')
        selftext = post_data.get('selftext', '')
        full_text = f"{title} {selftext}"
        
        relevance = self.calculate_relevance_score(full_text)
        
        # Include all posts - we'll filter later
        return {
            'id': post_data.get('id', ''),
            'subreddit': subreddit_name,
            'title': title,
            'selftext': selftext[:2000] if selftext else '',
            'url': f"https://reddit.com{post_data.get('permalink', '')}",
            'score': post_data.get('score', 0),
            'num_comments': post_data.get('num_comments', 0),
            'created_utc': datetime.fromtimestamp(
                post_data.get('created_utc', 0), 
                tz=timezone.utc
            ),
            'author': post_data.get('author', '[deleted]'),
            'relevance': relevance,
            'flair': post_data.get('link_flair_text')
        }
    
    def get_post_comments(self, subreddit: str, post_id: str, 
                          limit: int = 20) -> List[Dict]:
        """Get comments from a specific post"""
        url = f"{self.base_url}/r/{subreddit}/comments/{post_id}.json?limit={limit}&sort=top"
        
        data = self._make_request(url)
        
        if not data or len(data) < 2:
            return []
        
        comments = []
        comment_data = data[1].get('data', {}).get('children', [])
        
        for child in comment_data[:limit]:
            if child.get('kind') != 't1':
                continue
                
            comment = child.get('data', {})
            body = comment.get('body', '')
            
            if body and body != '[deleted]' and body != '[removed]':
                relevance = self.calculate_relevance_score(body)
                comments.append({
                    'id': comment.get('id', ''),
                    'body': body[:1500],
                    'score': comment.get('score', 0),
                    'author': comment.get('author', '[deleted]'),
                    'created_utc': datetime.fromtimestamp(
                        comment.get('created_utc', 0),
                        tz=timezone.utc
                    ),
                    'relevance': relevance,
                    'is_op': comment.get('is_submitter', False)
                })
        
        # Sort by score
        comments.sort(key=lambda x: x['score'], reverse=True)
        return comments
    
    def scan_all_uae_subreddits(self, limit_per_sub: int = 30) -> List[Dict]:
        """Scan all UAE-related subreddits"""
        all_posts = []
        
        for subreddit in UAE_SUBREDDITS:
            try:
                print(f"📡 Scanning r/{subreddit}...")
                
                # Get new posts
                new_posts = self.scan_subreddit(subreddit, limit=limit_per_sub, sort='new')
                all_posts.extend(new_posts)
                print(f"   ✓ Found {len(new_posts)} posts")
                
                # Also get hot posts for engagement
                hot_posts = self.scan_subreddit(subreddit, limit=limit_per_sub//2, sort='hot')
                # Avoid duplicates
                existing_ids = {p['id'] for p in all_posts}
                for post in hot_posts:
                    if post['id'] not in existing_ids:
                        all_posts.append(post)
                        existing_ids.add(post['id'])
                
            except Exception as e:
                print(f"   ✗ Error scanning r/{subreddit}: {e}")
        
        return all_posts
    
    def sort_posts(self, posts: List[Dict], 
                   sort_by: str = 'relevance_date') -> List[Dict]:
        """Sort posts by various criteria"""
        if sort_by == 'relevance':
            return sorted(posts, key=lambda x: x['relevance']['combined'], reverse=True)
        elif sort_by == 'date':
            return sorted(posts, key=lambda x: x['created_utc'], reverse=True)
        elif sort_by == 'relevance_date':
            now = datetime.now(timezone.utc)
            def combined_score(post):
                days_old = (now - post['created_utc']).days
                recency_factor = max(0.1, 1 - (days_old / 30))
                return post['relevance']['combined'] * recency_factor + (post['score'] / 1000)
            return sorted(posts, key=combined_score, reverse=True)
        elif sort_by == 'engagement':
            return sorted(posts, key=lambda x: x['num_comments'] + x['score'], reverse=True)
        return posts
    
    def filter_by_relevance(self, posts: List[Dict], 
                           min_score: float = 0.1,
                           category: str = 'combined') -> List[Dict]:
        """Filter posts by minimum relevance score"""
        return [p for p in posts if p['relevance'].get(category, 0) >= min_score]


def main():
    """Test the scanner"""
    scanner = RedditScanner()
    
    print("\n🔍 Scanning UAE subreddits (no API needed)...\n")
    posts = scanner.scan_all_uae_subreddits(limit_per_sub=25)
    
    print(f"\n📊 Total posts found: {len(posts)}")
    
    # Sort and filter
    sorted_posts = scanner.sort_posts(posts, 'relevance_date')
    relevant_posts = scanner.filter_by_relevance(sorted_posts, min_score=0.1)
    
    print(f"📌 Relevant posts: {len(relevant_posts)}")
    
    print("\n" + "="*70)
    print("TOP 10 RELEVANT POSTS")
    print("="*70)
    
    for i, post in enumerate(relevant_posts[:10], 1):
        print(f"\n{i}. [{post['subreddit']}] {post['title'][:65]}...")
        print(f"   📈 Relevance: {post['relevance']['combined']:.2f} | "
              f"Legal: {post['relevance']['legal_matches']} | "
              f"Translation: {post['relevance']['translation_matches']}")
        print(f"   💬 Comments: {post['num_comments']} | ⬆️ Score: {post['score']}")
        print(f"   🔗 {post['url']}")
        
        # Get comments for top posts
        if post['num_comments'] > 0 and i <= 3:
            print("\n   📝 Top comments:")
            comments = scanner.get_post_comments(post['subreddit'], post['id'], limit=3)
            for c in comments[:2]:
                preview = c['body'][:120].replace('\n', ' ')
                print(f"      • ({c['score']}↑) {preview}...")


if __name__ == '__main__':
    main()
