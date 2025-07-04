import boto3
import json
from typing import Dict, Any, List
from datetime import datetime
from report_service.core.config import settings

class UserS3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        self.bucket_name = settings.AWS_S3_BUCKET
    
    def upload_user_report(self, user_id: str, job_id: str, content: str, file_type: str = "json") -> str:
        """
        Upload user report (path: reports/{user_id}/{job_id}_report.{file_type})
        """
        try:
            key = f"reports/{user_id}/{job_id}_report.{file_type}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=f"application/{file_type}",
                Metadata={
                    "user_id": user_id,
                    "job_id": job_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            return key
        except Exception as e:
            raise Exception(f"Failed to upload report: {str(e)}")
    
    def upload_user_audio(self, user_id: str, job_id: str, audio_data: bytes) -> str:
        """
        Upload user-specific audio file
        """
        try:
            key = f"audio/{user_id}/{job_id}_audio.mp3"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=audio_data,
                ContentType="audio/mpeg",
                Metadata={
                    "user_id": user_id,
                    "job_id": job_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            return key
        except Exception as e:
            raise Exception(f"Failed to upload audio: {str(e)}")
  
    def get_user_files(self, user_id: str, file_type: str = None) -> List[Dict]:
        """
        List user files (reports, audio, visuals)
        """
        try:
            prefix = f"{file_type}/{user_id}/" if file_type else f"{user_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            files = []
            for obj in response.get('Contents', []):
                metadata_response = self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=obj['Key']
                )
                files.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "metadata": metadata_response.get('Metadata', {})
                })
            return files
        except Exception as e:
            raise Exception(f"Failed to list user files: {str(e)}")
    
    def get_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Generate presigned URL for download
        """
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
    
    def upload_text_content(self, s3_key: str, content: str) -> str:
        """
        Upload plain text content to S3
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType="text/plain",
                Metadata={
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            return s3_key
        except Exception as e:
            raise Exception(f"Failed to upload text content: {str(e)}")
    
    def get_file_content(self, s3_key: str) -> str:
        """
        Retrieve file content from S3
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"Failed to get file content: {str(e)}")
            return ""
    
    def delete_user_file(self, s3_key: str):
        """
        Delete a user file from S3
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")

user_s3_service = UserS3Service()
