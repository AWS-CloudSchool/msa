import boto3
import os
from core.config import settings

class S3Service:
    def __init__(self):
        # Initialize S3 client with credentials and region
        self.s3_client = boto3.client(
            's3', 
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket_name = settings.AWS_S3_BUCKET
        print(f"[S3 INIT] Initialized S3 client with bucket={self.bucket_name}, region={settings.AWS_REGION}")

    def upload_file(self, file_path, object_name=None, content_type=None, acl="public-read"):
        """
        Upload a file to S3 bucket.
        Returns the public URL if successful, or an error message string.
        """
        try:
            if object_name is None:
                object_name = os.path.basename(file_path)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            file_size = os.path.getsize(file_path)
            extra_args = {"ACL": acl}
            if content_type:
                extra_args["ContentType"] = content_type
            print(f"[S3 UPLOAD] Uploading: {file_path} to {object_name} (size: {file_size} bytes)")
            with open(file_path, 'rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data,
                    self.bucket_name,
                    object_name,
                    ExtraArgs=extra_args
                )
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_name}"
            print(f"[S3 UPLOAD] Upload successful: {url}")
            return url
        except Exception as e:
            error_msg = f"[S3 UPLOAD ERROR]: {str(e)}"
            print(error_msg)
            return f"[S3 upload failed: {str(e)}]"

    def list_objects(self, prefix="", max_keys=100):
        """List objects in S3 bucket with optional prefix and limit."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            if 'Contents' in response:
                return response['Contents']
            return []
        except Exception as e:
            print(f"[S3 LIST ERROR]: {str(e)}")
            return []

    def get_file_content(self, object_name: str) -> str:
        """Retrieve file content from S3 as UTF-8 string."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            content = response['Body'].read().decode('utf-8')
            print(f"[S3 READ] Successfully read: {object_name}")
            return content
        except Exception as e:
            print(f"[S3 READ ERROR] Failed to read: {object_name} - {str(e)}")
            return ""

# Singleton instance
s3_service = S3Service()
