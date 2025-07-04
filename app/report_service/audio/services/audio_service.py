import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from core.config import settings
from s3.services.s3_service import s3_service

class AudioService:
    def __init__(self):
        self.polly_client = boto3.client('polly', region_name=settings.AWS_REGION)
        self.voice_id = settings.POLLY_VOICE_ID

    async def generate_audio(self, text: str, job_id: str, voice_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate audio using Polly from input text"""
        try:
            voice_id = voice_id or self.voice_id

            # Polly limit: max 3000 characters
            if len(text) > 3000:
                chunks = [text[i:i+2800] for i in range(0, len(text), 2800)]
                audio_parts = []

                for i, chunk in enumerate(chunks):
                    response = self.polly_client.synthesize_speech(
                        Text=chunk,
                        OutputFormat='mp3',
                        VoiceId=voice_id,
                        Engine='neural' if voice_id in ['Seoyeon'] else 'standard'
                    )
                    audio_parts.append(response['AudioStream'].read())

                audio_data = b''.join(audio_parts)
            else:
                response = self.polly_client.synthesize_speech(
                    Text=text,
                    OutputFormat='mp3',
                    VoiceId=voice_id,
                    Engine='neural' if voice_id in ['Seoyeon'] else 'standard'
                )
                audio_data = response['AudioStream'].read()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_s3_key = f"audio/{timestamp}_{job_id}.mp3"

            s3_service.s3_client.put_object(
                Bucket=s3_service.bucket_name,
                Key=audio_s3_key,
                Body=audio_data,
                ContentType='audio/mpeg',
                Metadata={
                    'job-id': job_id,
                    'voice-id': voice_id,
                    'created-at': timestamp,
                    'text-length': str(len(text))
                }
            )

            return {
                "success": True,
                "audio_s3_key": audio_s3_key,
                "bucket": s3_service.bucket_name,
                "voice_id": voice_id,
                "audio_url": f"s3://{s3_service.bucket_name}/{audio_s3_key}",
                "size": len(audio_data),
                "duration_estimate": len(text) / 200  # approximate duration in seconds
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Polly audio generation failed: {str(e)}")

    async def stream_audio(self, audio_s3_key: str) -> StreamingResponse:
        """Stream audio file from S3"""
        try:
            response = s3_service.s3_client.get_object(
                Bucket=s3_service.bucket_name,
                Key=audio_s3_key
            )
            audio_stream = response['Body']

            def generate():
                try:
                    while True:
                        chunk = audio_stream.read(8192)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    audio_stream.close()

            return StreamingResponse(
                generate(),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"inline; filename={audio_s3_key.split('/')[-1]}",
                    "Accept-Ranges": "bytes"
                }
            )

        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Audio file not found: {str(e)}")

    async def find_audio_file(self, audio_id: str) -> str:
        """Find audio file in S3 by audio ID"""
        if not audio_id.endswith('.mp3'):
            response = s3_service.s3_client.list_objects_v2(
                Bucket=s3_service.bucket_name,
                Prefix=f"audio/",
                MaxKeys=100
            )

            for obj in response.get('Contents', []):
                if audio_id in obj['Key'] and obj['Key'].endswith('.mp3'):
                    return obj['Key']

            raise HTTPException(status_code=404, detail=f"Audio file not found: {audio_id}")

        return f"audio/{audio_id}"

audio_service = AudioService()
