# app/analyze/routers/youtube_analyze.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from report_service.analyze.core.auth import get_current_user
from report_service.database.core.database import get_db
from report_service.analyze.services.youtube_analyze_service import youtube_reporter_service
from report_service.database.services.database_service import database_service
from report_service.analyze.models.youtube_analyze import YouTubeReporterRequest, YouTubeReporterResponse
import logging

logger = logging.getLogger(__name__)

#prefix="/analyze",
router = APIRouter(prefix="/analyze", tags=["YouTube Reporter"])


async def run_youtube_analysis(job_id: str, user_id: str, youtube_url: str, db: Session):
    """ë°±ê·¸?¼ìš´?œì—??YouTube ë¶„ì„ ?¤í–‰"""
    try:
        await youtube_reporter_service.process_youtube_analysis(
            job_id=job_id,
            user_id=user_id,
            youtube_url=youtube_url,
            db=db
        )
    except Exception as e:
        logger.error(f"ë°±ê·¸?¼ìš´??YouTube ë¶„ì„ ?¤íŒ¨: {job_id} - {str(e)}")


@router.post("/youtube", response_model=YouTubeReporterResponse)
async def create_youtube_analysis(
        request: YouTubeReporterRequest,
        background_tasks: BackgroundTasks,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    YouTube ?ìƒ ë¶„ì„ ë°??¤ë§ˆ???œê°??ë¦¬í¬???ì„±

    - **youtube_url**: ë¶„ì„??YouTube ?ìƒ URL
    - **include_audio**: ?Œì„± ?”ì•½ ?ì„± ?¬ë? (? íƒ?¬í•­)
    - **options**: ì¶”ê? ?µì…˜ (? íƒ?¬í•­)
    """
    try:
        user_id = current_user["user_id"]
        youtube_url = request.youtube_url

        logger.info(f"?¬ YouTube Reporter ë¶„ì„ ?”ì²­: {youtube_url} (User: {user_id})")

        # 1. ?‘ì—… ?ì„±
        job_id = await youtube_reporter_service.create_analysis_job(
            user_id=user_id,
            youtube_url=youtube_url,
            db=db
        )

        # 2. ë°±ê·¸?¼ìš´?œì—??ë¶„ì„ ?¤í–‰
        background_tasks.add_task(
            run_youtube_analysis,
            job_id=job_id,
            user_id=user_id,
            youtube_url=youtube_url,
            db=db
        )

        return YouTubeReporterResponse(
            job_id=job_id,
            status="processing",
            message="?? YouTube Reporter ë¶„ì„???œì‘?˜ì—ˆ?µë‹ˆ?? AIê°€ ?ìƒ??ë¶„ì„?˜ê³  ?¤ë§ˆ???œê°?”ë? ?ì„±?˜ëŠ” ì¤‘ì…?ˆë‹¤...",
            estimated_time="2-5ë¶?
        )

    except Exception as e:
        logger.error(f"YouTube Reporter ë¶„ì„ ?”ì²­ ?¤íŒ¨: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"YouTube Reporter ë¶„ì„ ?œì‘ ?¤íŒ¨: {str(e)}"
        )


@router.get("/jobs/{job_id}/status")
async def get_analysis_status(
        job_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    YouTube Reporter ë¶„ì„ ?‘ì—… ?íƒœ ì¡°íšŒ

    - **job_id**: ?‘ì—… ID
    """
    try:
        user_id = current_user["user_id"]

        # ?°ì´?°ë² ?´ìŠ¤?ì„œ ?‘ì—… ?•ë³´ ì¡°íšŒ
        job = database_service.get_job_by_id(db, job_id, user_id)
        if not job:
            raise HTTPException(status_code=404, detail="?‘ì—…??ì°¾ì„ ???†ìŠµ?ˆë‹¤")

        # ì§„í–‰ë¥??•ë³´ ì¡°íšŒ
        progress_info = youtube_reporter_service.get_job_progress(job_id)

        return {
            "job_id": job_id,
            "status": job.status,
            "progress": progress_info.get("progress", 0),
            "message": progress_info.get("message", f"?íƒœ: {job.status}"),
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "input_data": job.input_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"?‘ì—… ?íƒœ ì¡°íšŒ ?¤íŒ¨: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"?‘ì—… ?íƒœ ì¡°íšŒ ?¤íŒ¨: {str(e)}"
        )


@router.get("/jobs/{job_id}/result")
async def get_analysis_result(
        job_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    YouTube Reporter ë¶„ì„ ê²°ê³¼ ì¡°íšŒ

    - **job_id**: ?‘ì—… ID
    """
    try:
        user_id = current_user["user_id"]

        # ?‘ì—… ?íƒœ ?•ì¸
        job = database_service.get_job_by_id(db, job_id, user_id)
        if not job:
            raise HTTPException(status_code=404, detail="?‘ì—…??ì°¾ì„ ???†ìŠµ?ˆë‹¤")

        if job.status == "processing":
            raise HTTPException(
                status_code=202,
                detail="?„ì§ ë¶„ì„ ì¤‘ì…?ˆë‹¤. ? ì‹œ ???¤ì‹œ ?œë„?´ì£¼?¸ìš”."
            )
        elif job.status == "failed":
            raise HTTPException(
                status_code=500,
                detail="ë¶„ì„???¤íŒ¨?ˆìŠµ?ˆë‹¤."
            )
        elif job.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"?‘ì—… ?íƒœ: {job.status}"
            )

        # ë³´ê³ ??ì¡°íšŒ
        reports = database_service.get_user_reports(db, user_id)
        job_report = next((r for r in reports if str(r.job_id) == job_id), None)

        if not job_report:
            raise HTTPException(status_code=404, detail="ë¶„ì„ ê²°ê³¼ë¥?ì°¾ì„ ???†ìŠµ?ˆë‹¤")

        # S3?ì„œ ë¦¬í¬???´ìš© ê°€?¸ì˜¤ê¸?        from report_service.s3.services.user_s3_service import user_s3_service
        import json

        try:
            download_url = user_s3_service.get_presigned_url(job_report.s3_key)
            
            # S3?ì„œ ë¦¬í¬???´ìš© ì¡°íšŒ
            report_content = None
            try:
                content = user_s3_service.get_file_content(job_report.s3_key)
                if content and job_report.file_type == 'json':
                    report_content = json.loads(content)
                    logger.info(f"S3?ì„œ ë¦¬í¬???´ìš© ì¡°íšŒ: {job_id}")
            except Exception as e:
                logger.warning(f"ë¦¬í¬???´ìš© ì¡°íšŒ ?¤íŒ¨: {e}")

            return {
                "job_id": job_id,
                "status": "completed",
                "title": job_report.title,
                "created_at": job_report.created_at.isoformat(),
                "download_url": download_url,
                "s3_key": job_report.s3_key,
                "file_type": job_report.file_type,
                "content": report_content,  # S3?ì„œ ì¡°íšŒ??ë¦¬í¬???´ìš©
                "message": "??YouTube Reporter ë¶„ì„???„ë£Œ?˜ì—ˆ?µë‹ˆ??"
            }

        except Exception as e:
            logger.error(f"S3 ê²°ê³¼ ì¡°íšŒ ?¤íŒ¨: {e}")
            raise HTTPException(
                status_code=500,
                detail="ë¶„ì„ ê²°ê³¼ ì¡°íšŒ ì¤??¤ë¥˜ê°€ ë°œìƒ?ˆìŠµ?ˆë‹¤"
            )


    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ë¶„ì„ ê²°ê³¼ ì¡°íšŒ ?¤íŒ¨: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ë¶„ì„ ê²°ê³¼ ì¡°íšŒ ?¤íŒ¨: {str(e)}"
        )


@router.get("/jobs")
async def list_my_analyses(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    ??YouTube Reporter ë¶„ì„ ?‘ì—… ëª©ë¡ ì¡°íšŒ (ë¡œê·¸??? íƒ??
    """
    try:
        # ë¡œê·¸?¸í•˜ì§€ ?Šì? ê²½ìš° ë¹?ëª©ë¡ ë°˜í™˜
        if not current_user:
            return {"jobs": [], "total": 0}
            
        user_id = current_user["user_id"]

        # YouTube Reporter ?‘ì—…ë§??„í„°ë§?        all_jobs = database_service.get_user_jobs(db, user_id)
        youtube_jobs = [job for job in all_jobs if job.job_type == "youtube_reporter"]

        return {
            "jobs": [
                {
                    "id": str(job.id),
                    "status": job.status,
                    "youtube_url": job.input_data.get("youtube_url", ""),
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in youtube_jobs
            ],
            "total": len(youtube_jobs)
        }

    except Exception as e:
        logger.error(f"?‘ì—… ëª©ë¡ ì¡°íšŒ ?¤íŒ¨: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"?‘ì—… ëª©ë¡ ì¡°íšŒ ?¤íŒ¨: {str(e)}"
        )


@router.delete("/jobs/{job_id}")
async def delete_analysis_job(
        job_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    YouTube Reporter ë¶„ì„ ?‘ì—… ?? œ

    - **job_id**: ?? œ???‘ì—… ID
    """
    try:
        user_id = current_user["user_id"]

        # ?‘ì—… ?? œ
        success = database_service.delete_job(db, job_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="?‘ì—…??ì°¾ì„ ???†ìŠµ?ˆë‹¤")

        return {"message": f"?‘ì—… {job_id}???? œ?˜ì—ˆ?µë‹ˆ??}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"?‘ì—… ?? œ ?¤íŒ¨: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"?‘ì—… ?? œ ?¤íŒ¨: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """YouTube Reporter ?œë¹„???íƒœ ?•ì¸"""
    try:
        return {
            "service": "YouTube Reporter",
            "status": "healthy",
            "version": "1.0.0",
            "features": {
                "smart_visualization": True,
                "comprehensive_summary": True,
                "context_analysis": True,
                "audio_generation": True
            },
            "supported_visualizations": [
                "charts", "network_diagrams", "flow_charts", "tables"
            ]
        }
    except Exception as e:
        logger.error(f"?¬ìŠ¤ì²´í¬ ?¤íŒ¨: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"?œë¹„???íƒœ ?•ì¸ ?¤íŒ¨: {str(e)}"
        )