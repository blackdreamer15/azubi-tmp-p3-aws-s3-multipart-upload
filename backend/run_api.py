#!/usr/bin/env python3
"""
Startup script for the S3 Multipart Upload API server
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Start the FastAPI server"""
    try:
        # Load environment variables
        try:
            from dotenv import load_dotenv
            # Try to load from production.env first, then fallback to .env
            if os.path.exists('production.env'):
                load_dotenv('production.env', override=True)
                print("✅ Environment variables loaded from production.env")
            else:
                load_dotenv(override=True)
                print("✅ Environment variables loaded from .env")
        except ImportError:
            print("⚠️ python-dotenv not available, using system environment")

        # Verify required environment variables
        required_vars = ['BUCKET_NAME', 'COGNITO_USER_POOL_ID', 'COGNITO_USER_POOL_CLIENT_ID']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("💡 Please check your production.env file or set these variables")
            return 1

        # Import and run the server
        import uvicorn

        print("🚀 Starting S3 Multipart Upload API server...")
        print("📖 API Documentation will be available at: http://localhost:8000/docs")
        print("📋 Alternative docs at: http://localhost:8000/redoc")
        print("⚡ Health check at: http://localhost:8000/health")

        # Run the server
        uvicorn.run(
            "src.api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Please install dependencies with: uv sync")
        return 1
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())