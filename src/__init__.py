"""
Reddit to LinkedIn Pipeline for OnlineTranslation.ae
"""

from .reddit_scanner import RedditScanner, UAE_SUBREDDITS, LEGAL_KEYWORDS, TRANSLATION_KEYWORDS
from .linkedin_generator import LinkedInPostGenerator
from .pipeline import RedditLinkedInPipeline

__all__ = [
    'RedditScanner',
    'LinkedInPostGenerator', 
    'RedditLinkedInPipeline',
    'UAE_SUBREDDITS',
    'LEGAL_KEYWORDS',
    'TRANSLATION_KEYWORDS'
]

__version__ = '1.0.0'
