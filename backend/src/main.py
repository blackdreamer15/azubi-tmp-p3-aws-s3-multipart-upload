"""
Main script for S3 Multipart Upload System
Demonstrates secure file upload with validation, monitoring, and security features
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from upload.multipart_uploader import S3MultipartUploader
from security.file_validator import FileValidator
from monitoring.security_monitor import SecurityMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning("python-dotenv not installed, using system environment variables")
    except Exception as e:
        logger.error(f"Failed to load environment variables: {e}")


def create_test_file(file_path: str, size_mb: int = 10) -> str:
    """Create a test file for demonstration purposes"""
    try:
        # Create test content
        content = b"0" * (1024 * 1024)  # 1MB of zeros

        with open(file_path, 'wb') as f:
            for _ in range(size_mb):
                f.write(content)

        logger.info(f"Created test file: {file_path} ({size_mb}MB)")
        return file_path
    except Exception as e:
        logger.error(f"Failed to create test file: {e}")
        raise


def upload_file(file_path: str, s3_key: Optional[str] = None, user_id: str = "demo_user") -> bool:
    """
    Upload a file using the multipart upload system
    Args:
        file_path: Path to the file to upload
        s3_key: Optional S3 key (defaults to filename)
        user_id: User identifier for logging
    Returns:
        True if upload successful, False otherwise
    """
    try:
        # Initialize components
        validator = FileValidator()
        uploader = S3MultipartUploader()
        monitor = SecurityMonitor()

        # Generate S3 key if not provided
        if not s3_key:
            s3_key = f"uploads/{user_id}/{os.path.basename(file_path)}"

        logger.info(f"Starting upload process for: {file_path}")
        logger.info(f"S3 key: {s3_key}")

        # Step 1: Validate file
        logger.info("Step 1: Validating file...")
        validation_result = validator.validate_file(file_path)

        if not validation_result['valid']:
            logger.error(f"File validation failed: {validation_result['errors']}")
            monitor.log_upload_activity(user_id, s3_key, 0, "failed", {
                'validation_errors': validation_result['errors']
            })
            return False

        logger.info("✅ File validation passed")
        logger.info(f"File info: {validation_result['file_info']}")

        # Step 2: Log upload initiation
        logger.info("Step 2: Logging upload initiation...")
        file_size = validation_result['file_info']['size']
        monitor.log_upload_activity(user_id, s3_key, file_size, "initiated", {
            'file_hash': validation_result['file_info'].get('sha256_hash'),
            'validation_passed': True
        })

        # Step 3: Perform upload
        logger.info("Step 3: Starting multipart upload...")
        upload_result = uploader.upload_large_file(
            file_path=file_path,
            s3_key=s3_key,
            metadata={
                'user_id': user_id,
                'file_hash': validation_result['file_info'].get('sha256_hash', ''),
                'upload_timestamp': str(Path(file_path).stat().st_mtime)
            }
        )

        # Step 4: Log successful upload
        logger.info("Step 4: Logging successful upload...")
        monitor.log_upload_activity(user_id, s3_key, file_size, "completed", {
            'upload_result': upload_result,
            'total_parts': upload_result.get('total_parts', 0)
        })

        logger.info("✅ Upload completed successfully!")
        logger.info(f"Upload result: {upload_result}")

        return True

    except Exception as e:
        logger.error(f"Upload failed: {e}")

        # Log failed upload
        try:
            monitor = SecurityMonitor()
            monitor.log_upload_activity(user_id, s3_key or "unknown", 0, "failed", {
                'error': str(e)
            })
        except Exception as log_error:
            logger.error(f"Failed to log upload failure: {log_error}")

        return False


def monitor_security():
    """Demonstrate security monitoring capabilities"""
    try:
        logger.info("🔍 Running security monitoring...")

        monitor = SecurityMonitor()

        # Check bucket security
        logger.info("Checking bucket security configuration...")
        security_check = monitor.check_bucket_security()

        if security_check.get('issues'):
            logger.warning(f"Security issues found: {security_check['issues']}")
        else:
            logger.info("✅ Bucket security configuration is good")

        # Get upload statistics
        logger.info("Getting upload statistics...")
        stats = monitor.get_upload_statistics(hours_back=24)
        if stats:
            logger.info(f"Upload statistics (last 24h): {stats}")

        # Check for unauthorized access
        logger.info("Checking for unauthorized access attempts...")
        unauthorized_events = monitor.monitor_unauthorized_access(hours_back=24)
        if unauthorized_events:
            logger.warning(f"Found {len(unauthorized_events)} unauthorized access attempts")
            for event in unauthorized_events:
                logger.warning(f"Unauthorized access: {event}")
        else:
            logger.info("✅ No unauthorized access attempts found")

    except Exception as e:
        logger.error(f"Security monitoring failed: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='S3 Multipart Upload System')
    parser.add_argument('--file', '-f', help='File to upload')
    parser.add_argument('--s3-key', '-k', help='S3 key for the uploaded file')
    parser.add_argument('--user-id', '-u', default='demo_user', help='User ID for logging')
    parser.add_argument('--create-test-file', '-t', type=int, help='Create a test file of specified size (MB)')
    parser.add_argument('--monitor', '-m', action='store_true', help='Run security monitoring')
    parser.add_argument('--validate-only', '-v', action='store_true', help='Only validate file, do not upload')

    args = parser.parse_args()

    # Load environment variables
    load_environment()

    # Check required environment variables
    required_vars = ['BUCKET_NAME', 'KMS_KEY_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please ensure your .env file is properly configured")
        return 1

    try:
        if args.monitor:
            # Run security monitoring
            monitor_security()
            return 0

        if args.create_test_file:
            # Create test file
            test_file_path = f"test_file_{args.create_test_file}mb.bin"
            create_test_file(test_file_path, args.create_test_file)
            file_path = test_file_path
        elif args.file:
            file_path = args.file
        else:
            logger.error("Please specify a file to upload or use --create-test-file")
            return 1

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return 1

        if args.validate_only:
            # Only validate file
            logger.info(f"Validating file: {file_path}")
            validator = FileValidator()
            validation_result = validator.validate_file(file_path)

            print("\n" + "="*50)
            print("FILE VALIDATION RESULTS")
            print("="*50)
            print(f"File: {file_path}")
            print(f"Valid: {'✅ YES' if validation_result['valid'] else '❌ NO'}")

            if validation_result['file_info']:
                print(f"Size: {validation_result['file_info']['size']:,} bytes")
                print(f"Extension: {validation_result['file_info']['extension']}")
                if 'sha256_hash' in validation_result['file_info']:
                    print(f"SHA256: {validation_result['file_info']['sha256_hash']}")

            if validation_result['errors']:
                print(f"Errors: {validation_result['errors']}")

            if validation_result['security_checks'].get('warnings'):
                print(f"Security warnings: {validation_result['security_checks']['warnings']}")

            print("="*50)
            return 0 if validation_result['valid'] else 1

        # Upload file
        success = upload_file(file_path, args.s3_key, args.user_id)

        if success:
            logger.info("🎉 Upload completed successfully!")
            return 0
        else:
            logger.error("❌ Upload failed!")
            return 1

    except KeyboardInterrupt:
        logger.info("Upload cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)