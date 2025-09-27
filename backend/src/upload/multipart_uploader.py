"""
S3 Multipart Upload Implementation
Handles secure multipart uploads with encryption and monitoring
"""

import os
import boto3
import hashlib
import logging
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3MultipartUploader:
    """Handles S3 multipart uploads with security and monitoring"""
    
    def __init__(self):
        """Initialize the multipart uploader with AWS configuration"""
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('BUCKET_NAME')
        self.kms_key_id = os.getenv('KMS_KEY_ID')
        
        if not self.bucket_name:
            raise ValueError("BUCKET_NAME environment variable is required")
        
        # Initialize S3 client with Signature Version 4 for KMS compatibility
        try:
            from botocore.config import Config
            config = Config(
                signature_version='s3v4',
                region_name=self.aws_region
            )
            self.s3_client = boto3.client('s3', region_name=self.aws_region, config=config)
            self.kms_client = boto3.client('kms', region_name=self.aws_region)
        except NoCredentialsError:
            raise ValueError("AWS credentials not found. Please configure AWS CLI or set environment variables")
        
        # Configuration
        self.min_part_size = 5 * 1024 * 1024  # 5MB minimum
        self.max_part_size = 100 * 1024 * 1024  # 100MB maximum
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', 104857600))  # 100MB default
        
        logger.info(f"Initialized S3MultipartUploader for bucket: {self.bucket_name}")
    
    def initiate_multipart_upload(self, file_key: str, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Initiate a multipart upload
        
        Args:
            file_key: S3 object key for the file
            metadata: Optional metadata for the object
            
        Returns:
            Dictionary containing upload_id and other upload details
        """
        try:
            # Prepare upload parameters
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': file_key,
                'ServerSideEncryption': 'aws:kms',
                'SSEKMSKeyId': self.kms_key_id,
                'ContentType': self._get_content_type(file_key)
            }
            
            # Add metadata if provided
            if metadata:
                upload_params['Metadata'] = metadata
            
            # Initiate multipart upload
            response = self.s3_client.create_multipart_upload(**upload_params)
            upload_id = response['UploadId']
            
            logger.info(f"Initiated multipart upload for {file_key}, UploadId: {upload_id}")
            
            return {
                'upload_id': upload_id,
                'bucket': self.bucket_name,
                'key': file_key,
                'status': 'initiated',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"Failed to initiate multipart upload for {file_key}: {e}")
            raise
    
    def generate_presigned_url(self, file_key: str, upload_id: str, part_number: int, 
                             expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for uploading a part
        
        Args:
            file_key: S3 object key
            upload_id: Multipart upload ID
            part_number: Part number (1-based)
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL for uploading the part
        """
        try:
            # Prepare parameters for presigned URL
            # Note: upload_part doesn't support ServerSideEncryption parameters
            # These are only used during create_multipart_upload
            params = {
                'Bucket': self.bucket_name,
                'Key': file_key,
                'UploadId': upload_id,
                'PartNumber': part_number
            }
            
            url = self.s3_client.generate_presigned_url(
                'upload_part',
                Params=params,
                ExpiresIn=expires_in,
                HttpMethod='PUT'
            )
            
            logger.info(f"Generated presigned URL for part {part_number} of {file_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def upload_part(self, file_path: str, file_key: str, upload_id: str, 
                   part_number: int, start_byte: int, end_byte: int) -> Dict[str, Any]:
        """
        Upload a single part of the file
        
        Args:
            file_path: Local file path
            file_key: S3 object key
            upload_id: Multipart upload ID
            part_number: Part number (1-based)
            start_byte: Start byte position in file
            end_byte: End byte position in file
            
        Returns:
            Dictionary containing ETag and part number
        """
        try:
            # Read the file part
            with open(file_path, 'rb') as file:
                file.seek(start_byte)
                part_data = file.read(end_byte - start_byte + 1)
            
            # Upload the part
            response = self.s3_client.upload_part(
                Bucket=self.bucket_name,
                Key=file_key,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=part_data
            )
            
            etag = response['ETag']
            logger.info(f"Uploaded part {part_number} of {file_key}, ETag: {etag}")
            
            return {
                'ETag': etag,
                'PartNumber': part_number
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload part {part_number}: {e}")
            raise
        except IOError as e:
            logger.error(f"Failed to read file part: {e}")
            raise
    
    def complete_multipart_upload(self, file_key: str, upload_id: str, 
                                 parts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Complete the multipart upload
        
        Args:
            file_key: S3 object key
            upload_id: Multipart upload ID
            parts: List of parts with ETag and PartNumber
            
        Returns:
            Dictionary containing completion details
        """
        try:
            # Sort parts by part number
            parts.sort(key=lambda x: x['PartNumber'])
            
            # Complete multipart upload
            response = self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=file_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            location = response['Location']
            etag = response['ETag']
            
            logger.info(f"Completed multipart upload for {file_key}, Location: {location}")
            
            return {
                'status': 'completed',
                'location': location,
                'etag': etag,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"Failed to complete multipart upload: {e}")
            raise
    
    def abort_multipart_upload(self, file_key: str, upload_id: str) -> Dict[str, Any]:
        """
        Abort a multipart upload
        
        Args:
            file_key: S3 object key
            upload_id: Multipart upload ID
            
        Returns:
            Dictionary containing abort details
        """
        try:
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket_name,
                Key=file_key,
                UploadId=upload_id
            )
            
            logger.info(f"Aborted multipart upload for {file_key}")
            
            return {
                'status': 'aborted',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"Failed to abort multipart upload: {e}")
            raise
    
    def upload_large_file(self, file_path: str, s3_key: str, 
                         metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a large file using multipart upload
        
        Args:
            file_path: Local file path
            s3_key: S3 object key
            metadata: Optional metadata
            
        Returns:
            Dictionary containing upload results
        """
        try:
            # Validate file
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise ValueError(f"File size {file_size} exceeds maximum allowed size {self.max_file_size}")
            
            # Calculate optimal part size
            part_size = self._calculate_part_size(file_size)
            total_parts = (file_size + part_size - 1) // part_size
            
            logger.info(f"Starting multipart upload: {file_path} -> {s3_key}")
            logger.info(f"File size: {file_size} bytes, Part size: {part_size} bytes, Total parts: {total_parts}")
            
            # Initiate multipart upload
            upload_info = self.initiate_multipart_upload(s3_key, metadata)
            upload_id = upload_info['upload_id']
            
            parts = []
            
            try:
                # Upload parts
                for part_number in range(1, total_parts + 1):
                    start_byte = (part_number - 1) * part_size
                    end_byte = min(start_byte + part_size - 1, file_size - 1)
                    
                    logger.info(f"Uploading part {part_number}/{total_parts}")
                    
                    part_info = self.upload_part(
                        file_path, s3_key, upload_id, part_number, start_byte, end_byte
                    )
                    parts.append(part_info)
                
                # Complete multipart upload
                result = self.complete_multipart_upload(s3_key, upload_id, parts)
                result.update({
                    'file_path': file_path,
                    's3_key': s3_key,
                    'file_size': file_size,
                    'total_parts': total_parts,
                    'part_size': part_size
                })
                
                logger.info(f"Successfully uploaded {file_path} to {s3_key}")
                return result
                
            except Exception as e:
                # Abort upload on error
                logger.error(f"Upload failed, aborting: {e}")
                self.abort_multipart_upload(s3_key, upload_id)
                raise
                
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise
    
    def _calculate_part_size(self, file_size: int) -> int:
        """Calculate optimal part size for multipart upload"""
        # Use 5MB for files up to 50MB, then scale up
        if file_size <= 50 * 1024 * 1024:
            return self.min_part_size
        else:
            # Use larger parts for bigger files, but cap at max_part_size
            optimal_size = max(self.min_part_size, min(file_size // 1000, self.max_part_size))
            return optimal_size
    
    def _get_content_type(self, file_key: str) -> str:
        """Get content type based on file extension"""
        extension = os.path.splitext(file_key)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.mp4': 'video/mp4',
            '.mp3': 'audio/mpeg',
            '.zip': 'application/zip',
            '.txt': 'text/plain',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return content_types.get(extension, 'application/octet-stream')
