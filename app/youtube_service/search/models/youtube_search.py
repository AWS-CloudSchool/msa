from pydantic import BaseModel, Field
from typing import List, Optional

class YouTubeSearchRequest(BaseModel):
    """YouTube 검색 요청 / YouTube search request"""
    query: str = Field(..., description="검색어 / Search keyword")
    max_results: int = Field(10, description="최대 결과 수 / Maximum number of results", ge=1, le=50)

class YouTubeVideoInfo(BaseModel):
    video_id: str = Field(..., description="비디오 ID / Video ID")
    title: str = Field(..., description="비디오 제목 / Video title")
    description: str = Field(..., description="비디오 설명 / Video description")
    channel_title: str = Field(..., description="채널 제목 / Channel title")
    published_at: str = Field(..., description="게시일 / Published date")
    view_count: int = Field(..., description="조회수 / View count")
    like_count: int = Field(..., description="좋아요 수 / Like count")
    comment_count: int = Field(..., description="댓글 수 / Comment count")
    duration: str = Field(..., description="재생 시간 / Video duration")
    thumbnail_url: str = Field(..., description="썸네일 URL / Thumbnail URL")

class YouTubeSearchResponse(BaseModel):
    query: str = Field(..., description="검색 쿼리 / Search query")
    total_results: int = Field(..., description="전체 검색 결과 수 / Total number of results")
    videos: List[YouTubeVideoInfo] = Field(..., description="검색된 비디오 목록 / List of found videos")
    next_page_token: Optional[str] = Field(None, description="다음 페이지 토큰 / Next page token")
