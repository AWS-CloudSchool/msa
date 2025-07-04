# app/agents/caption_agent.py

import requests
from langchain_core.runnables import Runnable
from core.config import settings
from analyze.services.state_manager import state_manager
from s3.services.user_s3_service import user_s3_service
import logging

logger = logging.getLogger(__name__)


class CaptionAgent(Runnable):
    def __init__(self):
        self.api_key = settings.VIDCAP_API_KEY
        self.api_url = "https://vidcap.xyz/api/v1/youtube/caption"

    def invoke(self, state: dict, config=None):
        youtube_url = state.get("youtube_url")
        job_id = state.get("job_id")
        user_id = state.get("user_id")

        logger.info(f"Caption extraction started for URL: {youtube_url}")

        if job_id:
            try:
                state_manager.update_progress(job_id, 20, "Extracting caption from YouTube...")
            except Exception as e:
                logger.warning(f"Failed to update progress (reason: {e})")

        try:
            response = requests.get(
                self.api_url,
                params={"url": youtube_url, "locale": "ko"},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()

            caption = response.json().get("data", {}).get("content", "")
            if not caption:
                caption = "Caption not found."

            # Upload to S3 if valid
            if job_id and user_id and caption != "Caption not found.":
                try:
                    s3_key = f"captions/{user_id}/{job_id}_caption.txt"
                    user_s3_service.upload_text_content(s3_key, caption)
                    logger.info(f"Caption uploaded to S3 at: {s3_key}")
                except Exception as e:
                    logger.warning(f"Failed to upload caption to S3 (reason: {e})")

            logger.info(f"Caption extraction completed. Length: {len(caption)}")
            return {**state, "caption": caption}

        except Exception as e:
            error_msg = f"Caption extraction failed: {str(e)}"
            logger.error(error_msg)
            return {**state, "caption": error_msg}
