"""
LinkedIn Post Generator
Crafts engaging LinkedIn posts from Reddit insights promoting OnlineTranslation.ae
"""

import os
from typing import List, Dict, Optional
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Note: anthropic package not installed. Install with: pip install anthropic")


class LinkedInPostGenerator:
    def __init__(self, api_key: str = None):
        """Initialize Claude API client"""
        self.client = None
        self.model = "claude-sonnet-4-20250514"
        
        if ANTHROPIC_AVAILABLE:
            api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
            else:
                print("Warning: No ANTHROPIC_API_KEY found. Set it to generate posts.")
    
    def generate_post(self, 
                      reddit_post: Dict,
                      comments: List[Dict],
                      style: str = 'professional',
                      include_cta: bool = True) -> Dict:
        """Generate a LinkedIn post from Reddit content"""
        
        if not self.client:
            raise RuntimeError(
                "Anthropic client not initialized. "
                "Install anthropic package and set ANTHROPIC_API_KEY."
            )
        
        # Prepare context from Reddit
        context = self._prepare_context(reddit_post, comments)
        
        # Build the prompt
        prompt = self._build_prompt(context, style, include_cta)
        
        # Generate with Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        post_content = response.content[0].text
        
        return {
            'content': post_content,
            'source_post': reddit_post['title'],
            'source_url': reddit_post['url'],
            'generated_at': datetime.now().isoformat(),
            'style': style
        }
    
    def _prepare_context(self, post: Dict, comments: List[Dict]) -> str:
        """Prepare context from Reddit post and comments"""
        context_parts = [
            f"ORIGINAL POST TITLE: {post['title']}",
            f"SUBREDDIT: r/{post['subreddit']}",
            f"ENGAGEMENT: {post['score']} upvotes, {post['num_comments']} comments",
        ]
        
        if post.get('selftext'):
            # Truncate long posts
            selftext = post['selftext'][:1000]
            context_parts.append(f"\nPOST CONTENT:\n{selftext}")
        
        if comments:
            context_parts.append("\nTOP INSIGHTS FROM COMMENTS:")
            for i, comment in enumerate(comments[:5], 1):
                # Get most upvoted, insightful comments
                if comment['score'] > 0:
                    body = comment['body'][:400]
                    context_parts.append(f"\n{i}. (Score: {comment['score']})\n{body}")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, context: str, style: str, include_cta: bool) -> str:
        """Build the prompt for LinkedIn post generation"""
        
        style_instructions = {
            'professional': """
Write in a professional, authoritative tone. Focus on providing value and 
establishing expertise. Use clear, concise language that appeals to business 
professionals and expats in the UAE.""",
            
            'empathetic': """
Write with empathy and understanding. Acknowledge the challenges people face 
with bureaucracy and paperwork in a new country. Be warm and supportive while 
offering solutions.""",
            
            'educational': """
Write in an educational, informative tone. Break down complex processes into 
simple steps. Help readers understand the "why" behind requirements.""",
            
            'storytelling': """
Use a storytelling approach. Start with a relatable scenario or common 
situation, then guide readers to the solution. Make it engaging and personal."""
        }
        
        cta_section = """
CALL TO ACTION:
End with a subtle but effective call to action that:
- Introduces OnlineTranslation.ae as a helpful resource
- Mentions their services: certified legal translations, document attestation, 
  Arabic-English translations, visa/legal document processing
- Feels natural, not salesy
- Invites engagement (comments, questions, DMs)
""" if include_cta else ""
        
        return f"""You are a LinkedIn content creator for OnlineTranslation.ae, a professional 
legal translation and document services company based in Dubai, UAE.

Based on this Reddit discussion from the UAE community, create an engaging LinkedIn post 
that addresses the topic/issue raised and positions OnlineTranslation.ae as a helpful solution.

REDDIT CONTEXT:
{context}

STYLE INSTRUCTIONS:
{style_instructions.get(style, style_instructions['professional'])}

{cta_section}

FORMATTING REQUIREMENTS:
1. Start with a hook - a question, bold statement, or relatable situation
2. Keep paragraphs short (2-3 sentences max) for mobile readability
3. Use line breaks between paragraphs for visual breathing room
4. Include 3-5 relevant emojis strategically placed (not overdone)
5. End with 8-12 relevant hashtags on a new line
6. Total length: 150-250 words (excluding hashtags)

HASHTAG SUGGESTIONS (choose relevant ones):
#DubaiLife #UAE #Expats #Dubai #AbuDhabi #LegalTranslation #ArabicTranslation 
#VisaUAE #DocumentAttestation #UAEBusiness #ExpatLife #DubaiExpats 
#LegalServices #Translation #CertifiedTranslation #MovingToDubai 
#UAEResidents #BusinessSetup #FreezoneUAE #GoldenVisa

Generate ONLY the LinkedIn post content. No explanations or meta-commentary."""
    
    def generate_batch(self, 
                       posts_with_comments: List[Dict],
                       styles: List[str] = None) -> List[Dict]:
        """Generate multiple LinkedIn posts from a batch of Reddit posts"""
        
        if styles is None:
            styles = ['professional', 'empathetic', 'educational', 'storytelling']
        
        generated_posts = []
        
        for i, item in enumerate(posts_with_comments):
            style = styles[i % len(styles)]  # Rotate through styles
            
            try:
                post = self.generate_post(
                    reddit_post=item['post'],
                    comments=item['comments'],
                    style=style
                )
                generated_posts.append(post)
                print(f"✓ Generated post {i+1}/{len(posts_with_comments)} ({style})")
            except Exception as e:
                print(f"✗ Error generating post {i+1}: {e}")
        
        return generated_posts
    
    def format_for_review(self, posts: List[Dict]) -> str:
        """Format generated posts for human review"""
        output = []
        
        for i, post in enumerate(posts, 1):
            output.append(f"\n{'='*60}")
            output.append(f"POST #{i} | Style: {post['style']}")
            output.append(f"Source: {post['source_post'][:60]}...")
            output.append(f"{'='*60}\n")
            output.append(post['content'])
            output.append(f"\n\n📎 Source: {post['source_url']}")
            output.append(f"🕐 Generated: {post['generated_at']}")
        
        return "\n".join(output)


# Topic-specific post templates
POST_TEMPLATES = {
    'visa_issues': {
        'hooks': [
            "🛂 Visa troubles in the UAE? You're not alone.",
            "The #1 reason visa applications get rejected in Dubai...",
            "After helping 1000+ clients with UAE visas, here's what I've learned:",
        ],
        'hashtags': '#VisaUAE #DubaiVisa #GoldenVisa #UAEResidency #Immigration'
    },
    'document_attestation': {
        'hooks': [
            "📄 The document attestation maze in UAE - let me simplify it for you.",
            "Why does every document need attestation in the UAE?",
            "MOFA, Embassy, Notary... confused about attestation? Here's the truth:",
        ],
        'hashtags': '#DocumentAttestation #MOFA #UAE #LegalDocuments #Apostille'
    },
    'arabic_translation': {
        'hooks': [
            "🔤 Lost in translation? Here's why accuracy matters in the UAE.",
            "The real cost of a bad Arabic translation...",
            "Not all translations are created equal. Here's what to look for:",
        ],
        'hashtags': '#ArabicTranslation #LegalTranslation #CertifiedTranslation #UAE'
    },
    'tenancy_issues': {
        'hooks': [
            "🏠 Tenant rights in Dubai - what you NEED to know.",
            "Your landlord can't do that! Know your rights in UAE.",
            "Ejari, RERA, deposit disputes - the tenant's survival guide:",
        ],
        'hashtags': '#DubaiRealEstate #TenantRights #RERA #Ejari #DubaiRentals'
    },
    'employment_law': {
        'hooks': [
            "⚖️ Leaving your job in UAE? Don't make these mistakes.",
            "Gratuity, notice period, labor ban - the exit checklist:",
            "Your UAE employment rights - what your employer won't tell you:",
        ],
        'hashtags': '#UAEEmployment #MOHRE #LaborLaw #DubaiJobs #GratuityUAE'
    }
}


def main():
    """Test the generator"""
    # Example Reddit post
    sample_post = {
        'id': 'test123',
        'subreddit': 'dubai',
        'title': 'Need help with document translation for visa application',
        'selftext': '''I need to get my university degree translated to Arabic for my 
work visa application. The typing center quoted me 500 AED but I've heard some 
translations get rejected. What should I look for? Does it need to be certified?
Any recommendations appreciated!''',
        'url': 'https://reddit.com/r/dubai/test123',
        'score': 45,
        'num_comments': 23,
        'relevance': {'combined': 0.8}
    }
    
    sample_comments = [
        {
            'body': '''Make sure you get a certified legal translation, not just any 
typing center translation. The Ministry of Justice needs specific formatting 
and it needs a translator stamp. I used OnlineTranslation.ae and they did it 
properly the first time.''',
            'score': 28
        },
        {
            'body': '''Don't cheap out on this. I got a translation from a random 
typing center and MOHRE rejected it twice. Ended up costing me more in delays 
and visa fees than the proper translation would have cost.''',
            'score': 15
        }
    ]
    
    generator = LinkedInPostGenerator()
    
    print("Generating LinkedIn post from Reddit content...\n")
    post = generator.generate_post(sample_post, sample_comments, style='empathetic')
    
    print("="*60)
    print("GENERATED LINKEDIN POST")
    print("="*60)
    print(post['content'])
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
