"""
Reddit Scanner using Web Search (Alternative for Cloud Environments)
When direct Reddit access is blocked, use this web search approach
"""

import subprocess
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Same keywords as main scanner
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


class WebSearchRedditScanner:
    """
    Alternative Reddit scanner using web search results.
    Use this when direct Reddit API/scraping is blocked (e.g., cloud environments).
    """
    
    def __init__(self):
        # Check if we can import the search functionality
        self.search_available = True
    
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
    
    def get_search_queries(self) -> List[str]:
        """Generate search queries for finding relevant Reddit content"""
        return [
            'site:reddit.com/r/dubai visa translation document',
            'site:reddit.com/r/dubai legal attestation certificate',
            'site:reddit.com/r/dubai arabic translation certified',
            'site:reddit.com/r/abudhabi visa document translation',
            'site:reddit.com/r/UAE legal document attestation',
            'site:reddit.com/r/dubai ejari tenancy contract',
            'site:reddit.com/r/dubai MOHRE labor employment',
            'site:reddit.com/r/dubai golden visa freelance',
            'site:reddit.com/r/dubai typing center translation',
            'site:reddit.com/r/dubai embassy attestation MOFA',
        ]
    
    def parse_reddit_url(self, url: str) -> Optional[Dict]:
        """Parse Reddit URL to extract subreddit and post ID"""
        # Match patterns like reddit.com/r/dubai/comments/abc123/title
        pattern = r'reddit\.com/r/(\w+)/comments/(\w+)'
        match = re.search(pattern, url)
        if match:
            return {
                'subreddit': match.group(1),
                'post_id': match.group(2)
            }
        return None
    
    def process_search_result(self, result: Dict) -> Optional[Dict]:
        """Process a search result into our post format"""
        url = result.get('url', '')
        parsed = self.parse_reddit_url(url)
        
        if not parsed:
            return None
        
        title = result.get('title', '').replace(' : r/' + parsed['subreddit'], '')
        snippet = result.get('snippet', '')
        full_text = f"{title} {snippet}"
        
        relevance = self.calculate_relevance_score(full_text)
        
        return {
            'id': parsed['post_id'],
            'subreddit': parsed['subreddit'],
            'title': title,
            'selftext': snippet,
            'url': url,
            'score': 0,  # Not available from search
            'num_comments': 0,  # Not available from search
            'created_utc': datetime.now(timezone.utc),  # Approximate
            'author': '[from search]',
            'relevance': relevance,
            'flair': None,
            'source': 'web_search'
        }


# Demo data for testing when Reddit is blocked
DEMO_POSTS = [
    {
        'id': 'demo1',
        'subreddit': 'dubai',
        'title': 'Need help with document translation for visa renewal - certified vs regular?',
        'selftext': '''I need to get my university degree translated to Arabic for my work visa renewal. 
The typing center near me quoted 500 AED but my PRO said some translations get rejected by MOHRE.
What should I look for? Does it need to be certified? Any recommendations for reliable translators?''',
        'url': 'https://reddit.com/r/dubai/comments/demo1/need_help_with_document_translation',
        'score': 45,
        'num_comments': 23,
        'created_utc': datetime.now(timezone.utc),
        'author': 'expat_question',
        'relevance': {'combined': 0.83, 'legal': 0.6, 'translation': 1.0, 'legal_matches': 3, 'translation_matches': 4},
        'flair': 'Question'
    },
    {
        'id': 'demo2',
        'subreddit': 'dubai',
        'title': 'Ejari registration rejected - landlord issues with tenancy contract',
        'selftext': '''My Ejari application was rejected because there are discrepancies between English and 
Arabic versions of my tenancy contract. The landlord got it translated cheaply and now there are errors.
Who is responsible for fixing this? Can I demand the landlord pay for proper translation?''',
        'url': 'https://reddit.com/r/dubai/comments/demo2/ejari_registration_rejected',
        'score': 67,
        'num_comments': 41,
        'created_utc': datetime.now(timezone.utc),
        'author': 'tenant_troubles',
        'relevance': {'combined': 0.67, 'legal': 0.8, 'translation': 0.67, 'legal_matches': 4, 'translation_matches': 2},
        'flair': 'Housing'
    },
    {
        'id': 'demo3',
        'subreddit': 'dubai',
        'title': 'Golden Visa application - which documents need Arabic translation?',
        'selftext': '''Starting my Golden Visa application as a property investor. The list of required documents 
is confusing. Do ALL documents need certified Arabic translation or just specific ones? My property deed 
is already bilingual but my bank statements and salary certificates are English only.''',
        'url': 'https://reddit.com/r/dubai/comments/demo3/golden_visa_application',
        'score': 89,
        'num_comments': 56,
        'created_utc': datetime.now(timezone.utc),
        'author': 'visa_applicant',
        'relevance': {'combined': 0.83, 'legal': 0.8, 'translation': 1.0, 'legal_matches': 4, 'translation_matches': 3},
        'flair': 'Visa'
    },
    {
        'id': 'demo4',
        'subreddit': 'abudhabi',
        'title': 'Police clearance certificate attestation for new job',
        'selftext': '''Got a job offer that requires police clearance certificate from my home country. 
It needs to be attested by MOFA and translated to Arabic. What's the process? Can I do this while 
still in UAE or do I need to go back? Any recommended attestation services?''',
        'url': 'https://reddit.com/r/abudhabi/comments/demo4/police_clearance_attestation',
        'score': 34,
        'num_comments': 19,
        'created_utc': datetime.now(timezone.utc),
        'author': 'job_seeker_ad',
        'relevance': {'combined': 0.83, 'legal': 0.6, 'translation': 1.0, 'legal_matches': 3, 'translation_matches': 4},
        'flair': 'Employment'
    },
    {
        'id': 'demo5',
        'subreddit': 'UAE',
        'title': 'Birth certificate translation and attestation for school admission',
        'selftext': '''Moving to Dubai with kids. School requires birth certificates with Arabic translation 
and UAE attestation. The certificates are from India. What's the full process and timeline? 
Anyone done this recently and can share the cost breakdown?''',
        'url': 'https://reddit.com/r/UAE/comments/demo5/birth_certificate_translation',
        'score': 52,
        'num_comments': 31,
        'created_utc': datetime.now(timezone.utc),
        'author': 'family_relocating',
        'relevance': {'combined': 1.0, 'legal': 0.4, 'translation': 1.0, 'legal_matches': 2, 'translation_matches': 5},
        'flair': 'Moving to UAE'
    }
]

DEMO_COMMENTS = {
    'demo1': [
        {
            'id': 'c1',
            'body': '''Definitely get a certified legal translation, not just any typing center. MOHRE and immigration 
are very strict about the format. I used a professional translation company and they knew exactly what stamps 
and formatting MOHRE requires. Cost a bit more (around 350 AED per page) but no rejections.''',
            'score': 28,
            'author': 'helpful_expat',
            'is_op': False
        },
        {
            'id': 'c2',
            'body': '''Made the mistake of going cheap on my degree translation. Got rejected twice by MOHRE which 
cost me way more in delays and visa extension fees than proper translation would have. The translator needs to 
be registered with the Ministry of Justice for legal documents.''',
            'score': 19,
            'author': 'learned_lesson',
            'is_op': False
        },
        {
            'id': 'c3',
            'body': '''Quick tip: ask if they can do the MOFA attestation as part of the service. Some companies 
handle the whole process end-to-end which saves you running around. Make sure translation includes translator 
stamp, signature, and MOJ registration number.''',
            'score': 15,
            'author': 'pro_advice',
            'is_op': False
        }
    ],
    'demo2': [
        {
            'id': 'c4',
            'body': '''Legally, the landlord should provide a proper bilingual contract. The Arabic version is the 
legally binding one in UAE courts, so any errors are a big problem. I would push back and demand they fix it 
at their expense - you shouldn't pay for their mistake.''',
            'score': 45,
            'author': 'legal_aware',
            'is_op': False
        },
        {
            'id': 'c5',
            'body': '''Had the same issue. RERA actually requires the contract to have matching Arabic and English. 
I contacted RERA and they put pressure on the landlord to provide corrected translation. Document everything 
in writing (email) for your protection.''',
            'score': 31,
            'author': 'rera_experience',
            'is_op': False
        }
    ],
    'demo3': [
        {
            'id': 'c6',
            'body': '''For Golden Visa, the requirements are: property deed (Title Deed) must be in Arabic already from 
DLD. Bank statements need certified translation. Salary certificates need translation AND employer attestation. 
Your passport obviously doesn't need translation. Budget around 1500-2000 AED for all translations if you have 
multiple documents.''',
            'score': 67,
            'author': 'golden_visa_holder',
            'is_op': False
        },
        {
            'id': 'c7',
            'body': '''One thing people miss: the translations need to be recent (within 3-6 months). Don't get them 
done too early. Also, ICA sometimes asks for additional documents at random, so keep some buffer time. 
I recommend doing all translations through one company so formatting is consistent.''',
            'score': 42,
            'author': 'visa_advisor',
            'is_op': False
        }
    ],
    'demo4': [
        {
            'id': 'c8',
            'body': '''You can do most of the process from UAE. Get your home country to apostille the police clearance, 
then courier it here. Then you need: 1) MOFA attestation 2) Certified Arabic translation 3) UAE notarization. 
Takes about 2-3 weeks if you use a service, or longer if doing yourself.''',
            'score': 23,
            'author': 'been_there',
            'is_op': False
        }
    ],
    'demo5': [
        {
            'id': 'c9',
            'body': '''Indian certificates process: 1) State HRD attestation in India 2) MEA attestation 3) UAE Embassy 
attestation in India 4) MOFA attestation in UAE 5) Arabic translation. Total cost around 5000-8000 AED depending 
on number of documents. Schools usually need this done within 30 days of admission.''',
            'score': 38,
            'author': 'indian_parent',
            'is_op': False
        },
        {
            'id': 'c10',
            'body': '''Pro tip: some attestation services offer package deals for families. Get all kids' birth 
certificates done together, saves money. Also, make sure translator keeps original spelling of names exactly 
as on certificate - any variation can cause issues later.''',
            'score': 25,
            'author': 'family_moved',
            'is_op': False
        }
    ]
}


def get_demo_data() -> tuple:
    """Return demo data for testing"""
    return DEMO_POSTS, DEMO_COMMENTS


if __name__ == '__main__':
    print("Demo data available for testing when Reddit is blocked.")
    print(f"Posts: {len(DEMO_POSTS)}")
    for post in DEMO_POSTS:
        print(f"  - [{post['subreddit']}] {post['title'][:50]}...")
