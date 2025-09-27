"""
Security Monitoring and Logging for S3 Multipart Upload
Monitors access patterns and detects unauthorized activity
"""

import os
import boto3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityMonitor:
    """Monitors S3 access and detects security threats"""
    
    def __init__(self):
        """Initialize the security monitor"""
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('BUCKET_NAME')
        self.log_group = os.getenv('CLOUDWATCH_LOG_GROUP', '/aws/s3-upload/dev')
        
        if not self.bucket_name:
            raise ValueError("BUCKET_NAME environment variable is required")
        
        # Initialize AWS clients
        try:
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.aws_region)
            self.cloudwatch_logs_client = boto3.client('logs', region_name=self.aws_region)
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
        except Exception as e:
            raise ValueError(f"Failed to initialize AWS clients: {e}")
        
        logger.info(f"Initialized SecurityMonitor for bucket: {self.bucket_name}")
    
    def log_upload_activity(self, user_id: str, file_key: str, file_size: int, 
                           upload_status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log upload activity to CloudWatch
        
        Args:
            user_id: Identifier for the user performing the upload
            file_key: S3 object key
            file_size: Size of the uploaded file
            upload_status: Status of the upload (initiated, completed, failed)
            metadata: Additional metadata
        """
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'upload_activity',
                'user_id': user_id,
                'file_key': file_key,
                'file_size': file_size,
                'upload_status': upload_status,
                'bucket_name': self.bucket_name,
                'metadata': metadata or {}
            }
            
            # Send to CloudWatch Logs
            self._send_to_cloudwatch_logs(log_entry)
            
            # Send custom metrics
            self._send_upload_metrics(user_id, file_size, upload_status)
            
            logger.info(f"Logged upload activity: {user_id} -> {file_key} ({upload_status})")
            
        except Exception as e:
            logger.error(f"Failed to log upload activity: {e}")
    
    def log_access_attempt(self, user_id: str, action: str, resource: str, 
                          success: bool, ip_address: Optional[str] = None) -> None:
        """
        Log access attempts for security monitoring
        
        Args:
            user_id: User identifier
            action: Action attempted (GET, PUT, DELETE, etc.)
            resource: Resource accessed
            success: Whether the action was successful
            ip_address: IP address of the request
        """
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'access_attempt',
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'success': success,
                'ip_address': ip_address,
                'bucket_name': self.bucket_name
            }
            
            # Send to CloudWatch Logs
            self._send_to_cloudwatch_logs(log_entry)
            
            # Check for suspicious activity
            if not success:
                self._check_suspicious_activity(user_id, action, resource, ip_address)
            
            logger.info(f"Logged access attempt: {user_id} -> {action} {resource} ({'SUCCESS' if success else 'FAILED'})")
            
        except Exception as e:
            logger.error(f"Failed to log access attempt: {e}")
    
    def monitor_unauthorized_access(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Monitor for unauthorized access attempts
        
        Args:
            hours_back: Number of hours to look back for unauthorized access
            
        Returns:
            List of unauthorized access events
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Query CloudWatch Logs for failed access attempts
            response = self.cloudwatch_logs_client.filter_log_events(
                logGroupName=self.log_group,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern='{ $.success = false }'
            )
            
            unauthorized_events = []
            for event in response.get('events', []):
                try:
                    log_data = json.loads(event['message'])
                    if log_data.get('event_type') == 'access_attempt' and not log_data.get('success'):
                        unauthorized_events.append({
                            'timestamp': log_data.get('timestamp'),
                            'user_id': log_data.get('user_id'),
                            'action': log_data.get('action'),
                            'resource': log_data.get('resource'),
                            'ip_address': log_data.get('ip_address')
                        })
                except json.JSONDecodeError:
                    continue
            
            logger.info(f"Found {len(unauthorized_events)} unauthorized access attempts in the last {hours_back} hours")
            return unauthorized_events
            
        except ClientError as e:
            logger.error(f"Failed to monitor unauthorized access: {e}")
            return []
    
    def get_upload_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get upload statistics for monitoring
        
        Args:
            hours_back: Number of hours to look back
            
        Returns:
            Dictionary containing upload statistics
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Query CloudWatch Logs for upload activities
            response = self.cloudwatch_logs_client.filter_log_events(
                logGroupName=self.log_group,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern='{ $.event_type = "upload_activity" }'
            )
            
            stats = {
                'total_uploads': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'total_size_uploaded': 0,
                'unique_users': set(),
                'uploads_by_status': {}
            }
            
            for event in response.get('events', []):
                try:
                    log_data = json.loads(event['message'])
                    if log_data.get('event_type') == 'upload_activity':
                        stats['total_uploads'] += 1
                        stats['total_size_uploaded'] += log_data.get('file_size', 0)
                        stats['unique_users'].add(log_data.get('user_id', 'unknown'))
                        
                        status = log_data.get('upload_status', 'unknown')
                        if status == 'completed':
                            stats['successful_uploads'] += 1
                        elif status == 'failed':
                            stats['failed_uploads'] += 1
                        
                        stats['uploads_by_status'][status] = stats['uploads_by_status'].get(status, 0) + 1
                        
                except json.JSONDecodeError:
                    continue
            
            # Convert set to count
            stats['unique_users'] = len(stats['unique_users'])
            
            logger.info(f"Upload statistics for last {hours_back} hours: {stats}")
            return stats
            
        except ClientError as e:
            logger.error(f"Failed to get upload statistics: {e}")
            return {}
    
    def check_bucket_security(self) -> Dict[str, Any]:
        """
        Check bucket security configuration
        
        Returns:
            Dictionary containing security check results
        """
        try:
            security_checks = {
                'bucket_exists': False,
                'versioning_enabled': False,
                'encryption_enabled': False,
                'public_access_blocked': False,
                'lifecycle_configured': False,
                'issues': []
            }
            
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                security_checks['bucket_exists'] = True
            except ClientError:
                security_checks['issues'].append("Bucket does not exist or is not accessible")
                return security_checks
            
            # Check versioning
            try:
                versioning = self.s3_client.get_bucket_versioning(Bucket=self.bucket_name)
                if versioning.get('Status') == 'Enabled':
                    security_checks['versioning_enabled'] = True
                else:
                    security_checks['issues'].append("Versioning is not enabled")
            except ClientError as e:
                security_checks['issues'].append(f"Could not check versioning: {e}")
            
            # Check encryption
            try:
                encryption = self.s3_client.get_bucket_encryption(Bucket=self.bucket_name)
                if encryption.get('ServerSideEncryptionConfiguration'):
                    security_checks['encryption_enabled'] = True
                else:
                    security_checks['issues'].append("Server-side encryption is not configured")
            except ClientError as e:
                security_checks['issues'].append(f"Could not check encryption: {e}")
            
            # Check public access block
            try:
                pab = self.s3_client.get_public_access_block(Bucket=self.bucket_name)
                pab_config = pab.get('PublicAccessBlockConfiguration', {})
                if all(pab_config.get(key, False) for key in ['BlockPublicAcls', 'BlockPublicPolicy', 'IgnorePublicAcls', 'RestrictPublicBuckets']):
                    security_checks['public_access_blocked'] = True
                else:
                    security_checks['issues'].append("Public access is not fully blocked")
            except ClientError as e:
                security_checks['issues'].append(f"Could not check public access block: {e}")
            
            # Check lifecycle configuration
            try:
                lifecycle = self.s3_client.get_bucket_lifecycle_configuration(Bucket=self.bucket_name)
                if lifecycle.get('Rules'):
                    security_checks['lifecycle_configured'] = True
                else:
                    security_checks['issues'].append("Lifecycle configuration is not set")
            except ClientError as e:
                security_checks['issues'].append(f"Could not check lifecycle configuration: {e}")
            
            logger.info(f"Security check completed for bucket {self.bucket_name}: {len(security_checks['issues'])} issues found")
            return security_checks
            
        except Exception as e:
            logger.error(f"Failed to check bucket security: {e}")
            return {'error': str(e)}
    
    def _send_to_cloudwatch_logs(self, log_entry: Dict[str, Any]) -> None:
        """Send log entry to CloudWatch Logs"""
        try:
            self.cloudwatch_logs_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=f"security-monitor-{datetime.utcnow().strftime('%Y-%m-%d')}",
                logEvents=[
                    {
                        'timestamp': int(datetime.utcnow().timestamp() * 1000),
                        'message': json.dumps(log_entry)
                    }
                ]
            )
        except ClientError as e:
            logger.error(f"Failed to send log to CloudWatch: {e}")
    
    def _send_upload_metrics(self, user_id: str, file_size: int, status: str) -> None:
        """Send custom metrics to CloudWatch"""
        try:
            self.cloudwatch_client.put_metric_data(
                Namespace='S3MultipartUpload',
                MetricData=[
                    {
                        'MetricName': 'UploadCount',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'User', 'Value': user_id},
                            {'Name': 'Status', 'Value': status}
                        ]
                    },
                    {
                        'MetricName': 'UploadSize',
                        'Value': file_size,
                        'Unit': 'Bytes',
                        'Dimensions': [
                            {'Name': 'User', 'Value': user_id}
                        ]
                    }
                ]
            )
        except ClientError as e:
            logger.error(f"Failed to send metrics to CloudWatch: {e}")
    
    def _check_suspicious_activity(self, user_id: str, action: str, resource: str, ip_address: Optional[str]) -> None:
        """Check for suspicious activity patterns"""
        try:
            # Log suspicious activity
            suspicious_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'suspicious_activity',
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'ip_address': ip_address,
                'severity': 'medium',
                'description': f"Failed {action} attempt on {resource}"
            }
            
            self._send_to_cloudwatch_logs(suspicious_entry)
            
            # Send alarm if multiple failed attempts
            # This is a simplified check - in production, you'd want more sophisticated pattern detection
            logger.warning(f"Suspicious activity detected: {user_id} failed {action} on {resource}")
            
        except Exception as e:
            logger.error(f"Failed to check suspicious activity: {e}")

    def get_recent_logs(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve recent log entries from CloudWatch Logs
        
        Args:
            hours: Number of hours back to search
            limit: Maximum number of log entries to return
            
        Returns:
            List of log entries with timestamps and details
        """
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Convert to milliseconds (CloudWatch expects milliseconds)
            start_timestamp = int(start_time.timestamp() * 1000)
            end_timestamp = int(end_time.timestamp() * 1000)
            
            # Query CloudWatch Logs
            response = self.cloudwatch_logs_client.filter_log_events(
                logGroupName=self.log_group,
                startTime=start_timestamp,
                endTime=end_timestamp,
                limit=limit
            )
            
            logs = []
            for event in response.get('events', []):
                try:
                    # Try to parse JSON log messages
                    message = event.get('message', '')
                    if message.startswith('{'):
                        log_data = json.loads(message)
                    else:
                        log_data = {'message': message}
                    
                    # Add CloudWatch metadata
                    log_data.update({
                        'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                        'ingestionTime': datetime.fromtimestamp(event['ingestionTime'] / 1000).isoformat(),
                        'logStreamName': event.get('logStreamName', 'unknown')
                    })
                    
                    logs.append(log_data)
                    
                except json.JSONDecodeError:
                    # If JSON parsing fails, create a simple log entry
                    logs.append({
                        'message': event.get('message', ''),
                        'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                        'logStreamName': event.get('logStreamName', 'unknown'),
                        'level': 'INFO'
                    })
            
            # Sort by timestamp (most recent first)
            logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            logger.info(f"Retrieved {len(logs)} log entries from the last {hours} hours")
            return logs
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.warning(f"Log group {self.log_group} not found")
                return []
            else:
                logger.error(f"CloudWatch Logs error: {e}")
                return []
        except Exception as e:
            logger.error(f"Failed to retrieve recent logs: {e}")
            return []

