import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from analyze.workflow.youtube_workflow import YouTubeReporterWorkflow
from database.services.database_service import database_service
from s3.services.user_s3_service import user_s3_service
from s3.services.s3_service import s3_service
from audio.services.audio_service import audio_service
from analyze.services.state_manager import state_manager
from analyze.services.youtube_metadata_service import youtube_metadata_service
import logging

logger = logging.getLogger(__name__)


class YouTubeReporterService:
    """YouTube Reporter analysis and report generation service"""

    def __init__(self):
        self.workflow = YouTubeReporterWorkflow()
        logger.info("YouTube Reporter service initialized")

    async def create_analysis_job(self, user_id: str, youtube_url: str, db: Session, include_audio: bool = True) -> str:
        """Create a new YouTube analysis job"""
        try:
            job = database_service.create_analysis_job(
                db=db,
                user_id=user_id,
                job_type="youtube_reporter",
                input_data={"youtube_url": youtube_url, "include_audio": include_audio}
            )
            job_id = str(job.id)
            logger.info(f"YouTube Reporter job created: {job_id}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to create analysis job: {str(e)}")
            raise

    async def process_youtube_analysis(self, job_id: str, user_id: str, youtube_url: str,
                                       db: Session, include_audio: bool = True) -> Dict[str, Any]:
        """Process the YouTube analysis job"""
        try:
            logger.info(f"Starting YouTube analysis: {job_id}")

            result = self.workflow.process(
                youtube_url=youtube_url,
                job_id=job_id,
                user_id=user_id
            )

            s3_info = await self._save_report_to_s3(
                user_id=user_id,
                job_id=job_id,
                result=result,
                youtube_url=youtube_url
            )

            audio_info = None
            if include_audio and result.get("success"):
                try:
                    audio_info = await self._generate_audio_summary(
                        user_id=user_id,
                        job_id=job_id,
                        summary=result.get("summary", "")
                    )
                except Exception as e:
                    logger.warning(f"Audio generation failed: {e}")
                    audio_info = {"success": False, "error": str(e)}

            database_service.update_job_status(
                db=db,
                job_id=job_id,
                status="completed" if result.get("success") else "failed",
                result_s3_key=s3_info.get("s3_key") if s3_info.get("success") else None
            )

            if s3_info.get("success"):
                database_service.create_user_report(
                    db=db,
                    job_id=job_id,
                    user_id=user_id,
                    title=result.get("title", "YouTube Analysis Report"),
                    s3_key=s3_info["s3_key"],
                    file_type="json"
                )

            if audio_info and audio_info.get("success"):
                database_service.create_user_audio(
                    db=db,
                    job_id=job_id,
                    user_id=user_id,
                    s3_key=audio_info["audio_s3_key"],
                    duration=audio_info.get("duration_estimate", 0)
                )

            try:
                state_manager.remove_user_active_job(user_id, job_id)
            except Exception as e:
                logger.warning(f"Failed to remove job from state manager: {e}")

            final_result = {
                **result,
                "s3_info": s3_info,
                "audio_info": audio_info,
                "job_id": job_id,
                "user_id": user_id,
                "completed_at": datetime.utcnow().isoformat()
            }

            logger.info(f"YouTube analysis completed: {job_id}")
            return final_result

        except Exception as e:
            logger.error(f"YouTube analysis failed: {job_id} - {str(e)}")
            database_service.update_job_status(db=db, job_id=job_id, status="failed")

            try:
                state_manager.remove_user_active_job(user_id, job_id)
            except Exception as redis_error:
                logger.warning(f"State cleanup failed: {redis_error}")

            raise

    async def _save_report_to_s3(self, user_id: str, job_id: str, result: Dict[str, Any],
                                 youtube_url: str) -> Dict[str, Any]:
        """Save analysis report to S3"""
        try:
            logger.info(f"Uploading report to S3 for job {job_id}")

            youtube_metadata = youtube_metadata_service.get_youtube_metadata(youtube_url)

            report_data = {
                "report": result,
                "metadata": {
                    "job_id": job_id,
                    "user_id": user_id,
                    "youtube_url": youtube_url,
                    "created_at": datetime.utcnow().isoformat(),
                    "service": "youtube_reporter",
                    "analysis_type": "youtube_analysis",
                    "status": "completed",
                    "youtube_title": youtube_metadata.get("youtube_title", ""),
                    "youtube_channel": youtube_metadata.get("youtube_channel", ""),
                    "youtube_duration": youtube_metadata.get("youtube_duration", ""),
                    "youtube_thumbnail": youtube_metadata.get("youtube_thumbnail", ""),
                    "video_id": youtube_metadata.get("video_id", "")
                }
            }

            s3_key = user_s3_service.upload_user_report(
                user_id=user_id,
                job_id=job_id,
                content=json.dumps(report_data, ensure_ascii=False, indent=2),
                file_type="json"
            )

            logger.info(f"S3 upload completed: {s3_key}")
            return {
                "success": True,
                "s3_key": s3_key,
                "bucket": user_s3_service.bucket_name
            }

        except Exception as e:
            logger.error(f"Failed to upload report to S3: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _generate_audio_summary(self, user_id: str, job_id: str, summary: str) -> Dict[str, Any]:
        """Generate audio summary using Polly"""
        try:
            logger.info(f"Starting audio generation for job {job_id}")

            if len(summary) > 2500:
                summary = summary[:2500] + "..."

            audio_result = await audio_service.generate_audio(
                text=summary,
                job_id=job_id,
                voice_id="Seoyeon"
            )

            if audio_result.get("success"):
                logger.info(f"Audio generation completed for job {job_id}")
                return audio_result
            else:
                logger.error(f"Audio generation failed: {audio_result}")
                return {"success": False, "error": "Audio generation failed"}

        except Exception as e:
            logger.error(f"Audio generation error: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_job_progress(self, job_id: str) -> Dict[str, Any]:
        """Get progress of analysis job"""
        try:
            progress = state_manager.get_progress(job_id)
            return progress or {"progress": 0, "message": "No progress available"}
        except Exception as e:
            logger.warning(f"Progress query failed: {e}")
            return {"progress": 0, "message": "Progress query failed"}


youtube_reporter_service = YouTubeReporterService()