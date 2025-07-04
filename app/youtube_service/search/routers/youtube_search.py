from fastapi import APIRouter, HTTPException, Body
from search.services.youtube_search_service import youtube_search_service
from search.models.youtube_search import YouTubeSearchRequest, YouTubeSearchResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["YouTube Search"])

@router.post("/youtube")
async def search_youtube_videos_post(
    request: YouTubeSearchRequest = Body(...)
) -> YouTubeSearchResponse:
    try:
        logger.info(f"YouTube search request (POST): query={request.query}, max_results={request.max_results}")
        
        result = await youtube_search_service.search_videos(
            query=request.query,
            max_results=request.max_results
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube search failed : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"YouTube search failed : {str(e)}"
        )