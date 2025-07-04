import re
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class YouTubeMetadataService:
    def __init__(self):
        pass

    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """Extract video ID from a YouTube URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        return None

    def get_youtube_metadata(self, youtube_url: str) -> Dict[str, Any]:
        """Retrieve metadata from a YouTube URL"""
        try:
            video_id = self.extract_video_id(youtube_url)
            if not video_id:
                logger.warning(f"Failed to extract video ID: {youtube_url}")
                return self._get_default_metadata(youtube_url)

            # Use YouTube oEmbed API (no API key required)
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

            try:
                response = requests.get(oembed_url, timeout=10)
                response.raise_for_status()
                data = response.json()

                # Construct thumbnail URL
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

                return {
                    "youtube_title": data.get("title", "Untitled"),
                    "youtube_channel": data.get("author_name", "Unknown Channel"),
                    "youtube_thumbnail": thumbnail_url,
                    "youtube_url": youtube_url,
                    "youtube_duration": "Unknown",  # not available from oEmbed
                    "video_id": video_id,
                    "created_at": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.warning(f"oEmbed API request failed: {e}")
                return self._get_default_metadata(youtube_url, video_id)

        except Exception as e:
            logger.error(f"Failed to extract YouTube metadata: {e}")
            return self._get_default_metadata(youtube_url)

    def _get_default_metadata(self, youtube_url: str, video_id: str = None) -> Dict[str, Any]:
        """Return default metadata if extraction fails"""
        thumbnail_url = ""
        if video_id:
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        return {
            "youtube_title": "YouTube Video",
            "youtube_channel": "Unknown",
            "youtube_thumbnail": thumbnail_url,
            "youtube_url": youtube_url,
            "youtube_duration": "Unknown",
            "video_id": video_id or "",
            "created_at": datetime.utcnow().isoformat()
        }

youtube_metadata_service = YouTubeMetadataService()
