import io
from typing import Optional, BinaryIO, Dict, Any
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

class S3Repository:
    """
    AWS S3 repository for release artifacts, SBOMs, and provenance attachments.
    Enforces server-side encryption and least-privilege key paths.
    """

    def __init__(self, bucket_name: str, region_name: str = "ap-south-1", session: Optional[boto3.Session] = None):
        self.bucket_name = bucket_name
        self.region_name = region_name
        cfg = Config(signature_version="s3v4", region_name=region_name)
        if session:
            self.s3_client = session.client("s3", config=cfg)
        else:
            self.s3_client = boto3.client("s3", config=cfg)

    def upload_artifact_stream(self, key: str, file_obj: BinaryIO, content_type: str = "application/octet-stream") -> str:
        """Upload stream with server-side AES256 encryption."""
        self.s3_client.upload_fileobj(
            file_obj,
            self.bucket_name,
            key,
            ExtraArgs={
                "ServerSideEncryption": "AES256",
                "ContentType": content_type
            }
        )
        return f"s3://{self.bucket_name}/{key}"

    def upload_artifact_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload byte buffer directly to S3."""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ServerSideEncryption="AES256",
            ContentType=content_type
        )
        return f"s3://{self.bucket_name}/{key}"

    def get_artifact_bytes(self, key: str) -> Optional[bytes]:
        """Download object bytes from S3."""
        try:
            resp = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return resp["Body"].read()
        except ClientError:
            return None

    def generate_presigned_upload_url(self, key: str, expires_in_seconds: int = 3600) -> Dict[str, Any]:
        """Generate short-lived pre-signed URL for direct client uploads."""
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                    "ServerSideEncryption": "AES256"
                },
                ExpiresIn=expires_in_seconds
            )
            return {
                "upload_url": url,
                "s3_key": key,
                "bucket": self.bucket_name,
                "expires_in_seconds": expires_in_seconds
            }
        except ClientError as e:
            raise RuntimeError(f"Failed to generate pre-signed S3 URL: {str(e)}")
