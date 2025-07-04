from typing import List
from datetime import datetime
from fastapi import HTTPException
from youtube_search import YoutubeSearch
from search.models.youtube_search import YouTubeSearchResponse, YouTubeVideoInfo
import re
import logging

logger = logging.getLogger(__name__)

class YouTubeSearchService:
    def __init__(self):
        pass

    async def search_videos(self, query: str, max_results: int = 10) -> YouTubeSearchResponse:
        """Search for YouTube videos based on a query"""
        try:
            logger.info(f"Starting YouTube search: query={query}, max_results={max_results}")
            
            # Perform search
            search_results = YoutubeSearch(
                query,
                max_results=max_results
            ).to_dict()

            logger.info(f"Number of results returned: {len(search_results)}")

            # Process response
            videos = []
            for item in search_results:
                try:
                    # Convert view count string to integer
                    views = item.get('views', '0')
                    views = int(re.sub(r'[^\d]', '', views)) if views else 0

                    # Convert duration string to seconds
                    duration = item.get('duration', '0:00')
                    duration_seconds = 0
                    
                    if duration and ':' in duration:
                        try:
                            duration_parts = duration.split(':')
                            if len(duration_parts) == 2:  # MM:SS
                                minutes, seconds = map(int, duration_parts)
                                duration_seconds = minutes * 60 + seconds
                            elif len(duration_parts) == 3:  # HH:MM:SS
                                hours, minutes, seconds = map(int, duration_parts)
                                duration_seconds = hours * 3600 + minutes * 60 + seconds
                        except ValueError:
                            duration_seconds = 0

                    # Filter out YouTube Shorts (duration ≤ 60 seconds)
                    if duration_seconds > 0 and duration_seconds <= 60:
                        logger.info(f"Skipping short video: {item['title']} ({duration_seconds} seconds)")
                        continue

                    video = YouTubeVideoInfo(
                        video_id=item['id'],
                        title=item['title'],
                        description=item.get('description', ''),
                        channel_title=item['channel'],
                        published_at=datetime.now().isoformat(),
                        view_count=views,
                        like_count=0,
                        comment_count=0,
                        duration=str(duration_seconds),
                        thumbnail_url=item['thumbnails'][0] if item.get('thumbnails') else ''
                    )
                    videos.append(video)
                except Exception as e:
                    logger.error(f"Error while converting video info: {str(e)}")
                    continue

            logger.info(f"Number of successfully parsed videos: {len(videos)}")

            return YouTubeSearchResponse(
                query=query,
                total_results=len(videos),
                videos=videos,
                next_page_token=None
            )

        except Exception as e:
            logger.error(f"YouTube search failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"YouTube search failed: {str(e)}"
            )

youtube_search_service = YouTubeSearchService()
