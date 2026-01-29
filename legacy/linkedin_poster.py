#!/usr/bin/env python3
"""
LinkedIn Posting Module

Supports multiple methods for posting to LinkedIn:

FREE OPTIONS:
1. Zapier Webhooks (Free tier: 100 tasks/month)
2. Make.com Webhooks (Free tier: 1000 ops/month)
3. LinkedIn Direct API (Free but complex, tokens expire every 60 days)

PAID OPTIONS:
4. Ayrshare API ($49/mo+ but easiest setup)

Note: Buffer API no longer accepts new developer apps (discontinued 2019).

Setup Instructions:
-------------------

OPTION 1: Zapier Webhooks (FREE - Recommended)
1. Create a Zapier account at https://zapier.com (free tier: 100 tasks/month)
2. Create a new Zap: Webhook (Catch Hook) → LinkedIn (Create Share Update)
3. Copy your webhook URL
4. Add to .env: ZAPIER_WEBHOOK_URL=your_webhook_url

OPTION 2: Make.com (FREE alternative)
1. Create account at https://make.com (free tier: 1000 ops/month)
2. Create scenario: Webhook → LinkedIn
3. Copy webhook URL
4. Add to .env: MAKE_WEBHOOK_URL=your_webhook_url

OPTION 3: LinkedIn Direct API (FREE but complex)
1. Create app at https://www.linkedin.com/developers/apps
2. Request 'w_member_social' permission
3. Complete OAuth2 flow
4. Add to .env: LINKEDIN_ACCESS_TOKEN=your_token
Note: Tokens expire every 60 days and require manual refresh

OPTION 4: Ayrshare API (PAID - $49/mo+, easiest)
1. Sign up at https://www.ayrshare.com
2. Connect your LinkedIn profile in dashboard
3. Copy your API Key from Settings
4. Add to .env: AYRSHARE_API_KEY=your_key_here
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()


class AyrsharePoster:
    """Post to LinkedIn via Ayrshare API (Paid - $49/mo+)."""

    BASE_URL = "https://app.ayrshare.com/api"

    def __init__(self):
        self.api_key = os.getenv("AYRSHARE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "AYRSHARE_API_KEY not found. "
                "Sign up at https://www.ayrshare.com (starts at $49/mo)"
            )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_profiles(self) -> List[Dict]:
        """Get connected social profiles."""
        url = f"{self.BASE_URL}/profiles"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json().get("profiles", [])

    def post_now(self, text: str, profile_id: Optional[str] = None) -> Dict:
        """Post immediately to LinkedIn."""
        url = f"{self.BASE_URL}/post"

        payload = {
            "post": text,
            "platforms": ["linkedin"]
        }

        if profile_id:
            payload["profileKey"] = profile_id

        response = requests.post(url, headers=self._headers(), json=payload)
        response.raise_for_status()
        return response.json()

    def schedule_post(
        self,
        text: str,
        scheduled_at: datetime,
        profile_id: Optional[str] = None
    ) -> Dict:
        """Schedule a post for later."""
        url = f"{self.BASE_URL}/post"

        payload = {
            "post": text,
            "platforms": ["linkedin"],
            "scheduleDate": scheduled_at.isoformat()
        }

        if profile_id:
            payload["profileKey"] = profile_id

        response = requests.post(url, headers=self._headers(), json=payload)
        response.raise_for_status()
        return response.json()

    def add_to_queue(self, text: str, profile_id: Optional[str] = None) -> Dict:
        """Add post to queue (posts at next available slot)."""
        # Ayrshare doesn't have a queue, so we post immediately
        return self.post_now(text, profile_id)

    def get_pending_posts(self, profile_id: Optional[str] = None) -> List[Dict]:
        """Get scheduled posts."""
        url = f"{self.BASE_URL}/history"
        params = {"status": "scheduled"}

        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json().get("posts", [])

    def delete_post(self, post_id: str) -> Dict:
        """Delete a scheduled post."""
        url = f"{self.BASE_URL}/post/{post_id}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
        return response.json()


class ZapierWebhookPoster:
    """Post to LinkedIn via Zapier Webhook."""

    def __init__(self):
        self.webhook_url = os.getenv("ZAPIER_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError(
                "ZAPIER_WEBHOOK_URL not found. "
                "Create a Zap at https://zapier.com with Webhook trigger → LinkedIn action"
            )

    def get_profiles(self) -> List[Dict]:
        """Webhooks don't have profile listing."""
        return [{"service": "linkedin", "formatted_username": "via Zapier", "id": "zapier"}]

    def post_now(self, text: str, profile_id: Optional[str] = None) -> Dict:
        """Send post to Zapier webhook."""
        payload = {
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "action": "post_now"
        }

        response = requests.post(self.webhook_url, json=payload)
        response.raise_for_status()

        return {"status": "sent_to_zapier", "text": text}

    def schedule_post(
        self,
        text: str,
        scheduled_at: datetime,
        profile_id: Optional[str] = None
    ) -> Dict:
        """Send scheduled post to Zapier (Zapier handles scheduling)."""
        payload = {
            "text": text,
            "scheduled_at": scheduled_at.isoformat(),
            "action": "schedule"
        }

        response = requests.post(self.webhook_url, json=payload)
        response.raise_for_status()

        return {"status": "sent_to_zapier", "scheduled_at": scheduled_at.isoformat()}

    def add_to_queue(self, text: str, profile_id: Optional[str] = None) -> Dict:
        """Same as post_now for webhooks."""
        return self.post_now(text, profile_id)

    def get_pending_posts(self, profile_id: Optional[str] = None) -> List[Dict]:
        """Webhooks don't track pending posts."""
        return []


class MakeWebhookPoster:
    """Post to LinkedIn via Make.com (Integromat) Webhook."""

    def __init__(self):
        self.webhook_url = os.getenv("MAKE_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError(
                "MAKE_WEBHOOK_URL not found. "
                "Create a scenario at https://make.com with Webhook → LinkedIn"
            )

    def get_profiles(self) -> List[Dict]:
        """Webhooks don't have profile listing."""
        return [{"service": "linkedin", "formatted_username": "via Make.com", "id": "make"}]

    def post_now(self, text: str, profile_id: Optional[str] = None) -> Dict:
        """Send post to Make webhook."""
        payload = {
            "text": text,
            "timestamp": datetime.now().isoformat()
        }

        response = requests.post(self.webhook_url, json=payload)
        response.raise_for_status()

        return {"status": "sent_to_make", "text": text}

    def schedule_post(
        self,
        text: str,
        scheduled_at: datetime,
        profile_id: Optional[str] = None
    ) -> Dict:
        """Send to Make with schedule info."""
        payload = {
            "text": text,
            "scheduled_at": scheduled_at.isoformat()
        }

        response = requests.post(self.webhook_url, json=payload)
        response.raise_for_status()

        return {"status": "sent_to_make", "scheduled_at": scheduled_at.isoformat()}

    def add_to_queue(self, text: str, profile_id: Optional[str] = None) -> Dict:
        return self.post_now(text, profile_id)

    def get_pending_posts(self, profile_id: Optional[str] = None) -> List[Dict]:
        return []


class LinkedInDirectPoster:
    """Post directly to LinkedIn API (requires partner approval)."""

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError(
                "LINKEDIN_ACCESS_TOKEN not found. "
                "See https://docs.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow"
            )
        self.person_id = os.getenv("LINKEDIN_PERSON_ID")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def get_profiles(self) -> List[Dict]:
        """Get user info."""
        try:
            user_info = self.get_user_info()
            return [{
                "service": "linkedin",
                "formatted_username": user_info.get("name", "LinkedIn User"),
                "id": user_info.get("sub")
            }]
        except Exception:
            return [{"service": "linkedin", "formatted_username": "Direct API", "id": "unknown"}]

    def get_user_info(self) -> Dict:
        """Get current user's LinkedIn info."""
        url = f"{self.BASE_URL}/userinfo"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def get_person_id(self) -> str:
        """Get the person URN for posting."""
        if self.person_id:
            return self.person_id
        user_info = self.get_user_info()
        return user_info.get("sub")

    def post_now(self, text: str, profile_id: Optional[str] = None) -> Dict:
        """Post text content to LinkedIn."""
        person_id = self.get_person_id()

        url = f"{self.BASE_URL}/ugcPosts"

        payload = {
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        response = requests.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        return response.json()

    def schedule_post(
        self,
        text: str,
        scheduled_at: datetime,
        profile_id: Optional[str] = None
    ) -> Dict:
        """LinkedIn API doesn't support scheduling."""
        raise ValueError("LinkedIn direct API doesn't support scheduling. Use Ayrshare or Zapier.")

    def add_to_queue(self, text: str, profile_id: Optional[str] = None) -> Dict:
        return self.post_now(text, profile_id)

    def get_pending_posts(self, profile_id: Optional[str] = None) -> List[Dict]:
        return []


# Legacy alias for backwards compatibility
BufferPoster = AyrsharePoster


def get_poster(method: str = "auto"):
    """
    Get the appropriate poster based on method or auto-detect from env vars.

    Args:
        method: "zapier", "make", "linkedin", "ayrshare", or "auto" (detect from env)

    Returns:
        Poster instance
    """
    if method == "auto":
        # Auto-detect based on available credentials (free options first)
        if os.getenv("ZAPIER_WEBHOOK_URL"):
            return ZapierWebhookPoster()
        elif os.getenv("MAKE_WEBHOOK_URL"):
            return MakeWebhookPoster()
        elif os.getenv("LINKEDIN_ACCESS_TOKEN"):
            return LinkedInDirectPoster()
        elif os.getenv("AYRSHARE_API_KEY"):
            return AyrsharePoster()
        else:
            raise ValueError(
                "No posting credentials found. Set one of:\n"
                "  FREE OPTIONS:\n"
                "  - ZAPIER_WEBHOOK_URL (100 tasks/month free)\n"
                "  - MAKE_WEBHOOK_URL (1000 ops/month free)\n"
                "  - LINKEDIN_ACCESS_TOKEN (free but complex)\n"
                "  PAID:\n"
                "  - AYRSHARE_API_KEY ($49/mo+)"
            )

    method_map = {
        "ayrshare": AyrsharePoster,
        "zapier": ZapierWebhookPoster,
        "make": MakeWebhookPoster,
        "linkedin": LinkedInDirectPoster,
        # Legacy support
        "buffer": AyrsharePoster,
    }

    if method not in method_map:
        raise ValueError(f"Unknown posting method: {method}. Use: {list(method_map.keys())}")

    return method_map[method]()


def post_to_linkedin(
    text: str,
    method: str = "auto",
    schedule_at: Optional[datetime] = None
) -> Dict:
    """
    Convenience function to post to LinkedIn.

    Args:
        text: The post content
        method: "ayrshare", "zapier", "make", "linkedin", or "auto"
        schedule_at: Optional datetime to schedule the post

    Returns:
        API response dict
    """
    poster = get_poster(method)

    if schedule_at:
        return poster.schedule_post(text, schedule_at)
    else:
        return poster.post_now(text)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Post to LinkedIn",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Methods (auto-detect order):
  zapier    - Zapier webhook (FREE - 100 tasks/month)
  make      - Make.com webhook (FREE - 1000 ops/month)
  linkedin  - LinkedIn direct API (FREE but complex)
  ayrshare  - Ayrshare API (PAID - $49/mo+)
  auto      - Auto-detect from environment variables

Examples:
  python linkedin_poster.py --list-profiles
  python linkedin_poster.py --text "Hello LinkedIn!"
  python linkedin_poster.py --file post.txt --method zapier
  python linkedin_poster.py --schedule 2025-01-30T10:00:00 --text "Scheduled!"
        """
    )
    parser.add_argument(
        "--method",
        choices=["ayrshare", "zapier", "make", "linkedin", "auto"],
        default="auto",
        help="Posting method (default: auto-detect)"
    )
    parser.add_argument("--text", help="Text to post")
    parser.add_argument("--file", help="File containing post text")
    parser.add_argument("--list-profiles", action="store_true", help="List connected profiles")
    parser.add_argument("--pending", action="store_true", help="Show pending/scheduled posts")
    parser.add_argument("--queue", action="store_true", help="Add to queue (same as post now)")
    parser.add_argument(
        "--schedule",
        help="Schedule post for later (ISO format: 2025-01-30T10:00:00)"
    )

    args = parser.parse_args()

    try:
        poster = get_poster(args.method)
        print(f"Using: {poster.__class__.__name__}")

        if args.list_profiles:
            profiles = poster.get_profiles()
            print("\nConnected profiles:")
            for p in profiles:
                print(f"  - {p.get('service')}: {p.get('formatted_username')} (ID: {p.get('id')})")
            exit(0)

        if args.pending:
            pending = poster.get_pending_posts()
            print(f"\nPending posts: {len(pending)}")
            for post in pending:
                text = post.get('post', post.get('text', ''))[:50]
                print(f"  - {text}...")
            exit(0)

        # Get text to post
        text = args.text
        if args.file:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()

        if not text:
            print("Error: Provide --text or --file")
            exit(1)

        # Post or schedule
        if args.schedule:
            scheduled_at = datetime.fromisoformat(args.schedule)
            result = poster.schedule_post(text, scheduled_at)
            print(f"Scheduled for {scheduled_at}")
        else:
            result = poster.post_now(text)
            print("Posted successfully!")

        print(f"Response: {json.dumps(result, indent=2)}")

    except Exception as e:
        print(f"Error: {e}")
        exit(1)
