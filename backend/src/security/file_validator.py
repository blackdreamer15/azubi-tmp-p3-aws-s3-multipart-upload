"""
File Validation and Security Checks
Validates file types, sizes, and content for secure uploads
"""

import os
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Try to import magic, fallback if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileValidator:
    """Validates files for security and compliance before upload"""
    
    def __init__(self):
        """Initialize the file validator"""
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', 104857600))  # 100MB default
        self.allowed_extensions = self._parse_allowed_types()
        self.allowed_mime_types = self._get_allowed_mime_types()
        
        # Security settings
        self.max_filename_length = 255
        self.forbidden_patterns = [
            '..',  # Directory traversal
            '/',   # Path separators
            '\\',  # Windows path separators
            '<', '>', ':', '"', '|', '?', '*',  # Invalid filename characters
        ]
        
        logger.info(f"Initialized FileValidator with max size: {self.max_file_size} bytes")
    
    def validate_file(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive file validation
        
        Args:
            file_path: Path to the file to validate
            filename: Optional filename (if different from file_path)
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'file_info': {},
            'security_checks': {}
        }
        
        try:
            # Basic file checks
            if not os.path.exists(file_path):
                validation_result['errors'].append("File does not exist")
                return validation_result
            
            if not os.path.isfile(file_path):
                validation_result['errors'].append("Path is not a file")
                return validation_result
            
            # Get file information
            file_info = self._get_file_info(file_path)
            validation_result['file_info'] = file_info
            
            # Validate file size
            size_validation = self._validate_file_size(file_path)
            if not size_validation['valid']:
                validation_result['errors'].extend(size_validation['errors'])
            
            # Validate filename
            filename_to_check = filename or os.path.basename(file_path)
            filename_validation = self._validate_filename(filename_to_check)
            if not filename_validation['valid']:
                validation_result['errors'].extend(filename_validation['errors'])
            
            # Validate file extension
            extension_validation = self._validate_extension(file_path)
            if not extension_validation['valid']:
                validation_result['errors'].extend(extension_validation['errors'])
            
            # Validate MIME type
            mime_validation = self._validate_mime_type(file_path)
            if not mime_validation['valid']:
                validation_result['errors'].extend(mime_validation['errors'])
            
            # Security checks
            security_checks = self._perform_security_checks(file_path)
            validation_result['security_checks'] = security_checks
            
            if security_checks.get('suspicious_content', False):
                validation_result['errors'].append("File contains suspicious content")
            
            # Calculate file hash for integrity
            file_hash = self._calculate_file_hash(file_path)
            validation_result['file_info']['sha256_hash'] = file_hash
            
            # Overall validation result
            validation_result['valid'] = len(validation_result['errors']) == 0
            
            if validation_result['valid']:
                logger.info(f"File validation passed: {file_path}")
            else:
                logger.warning(f"File validation failed: {file_path}, errors: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error during file validation: {e}")
            validation_result['errors'].append(f"Validation error: {str(e)}")
            return validation_result
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic file information"""
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'filename': os.path.basename(file_path),
                'extension': os.path.splitext(file_path)[1].lower(),
                'path': file_path
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {}
    
    def _validate_file_size(self, file_path: str) -> Dict[str, Any]:
        """Validate file size"""
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size == 0:
                return {'valid': False, 'errors': ['File is empty']}
            
            if file_size > self.max_file_size:
                return {
                    'valid': False, 
                    'errors': [f'File size {file_size} exceeds maximum allowed size {self.max_file_size}']
                }
            
            return {'valid': True, 'errors': []}
            
        except Exception as e:
            return {'valid': False, 'errors': [f'Could not determine file size: {e}']}
    
    def _validate_filename(self, filename: str) -> Dict[str, Any]:
        """Validate filename for security"""
        errors = []
        
        if not filename:
            errors.append("Filename is empty")
            return {'valid': False, 'errors': errors}
        
        if len(filename) > self.max_filename_length:
            errors.append(f"Filename too long (max {self.max_filename_length} characters)")
        
        # Check for forbidden patterns
        for pattern in self.forbidden_patterns:
            if pattern in filename:
                errors.append(f"Filename contains forbidden pattern: {pattern}")
        
        # Check for hidden files (starting with .)
        if filename.startswith('.'):
            errors.append("Hidden files are not allowed")
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    def _validate_extension(self, file_path: str) -> Dict[str, Any]:
        """Validate file extension"""
        try:
            extension = os.path.splitext(file_path)[1].lower()
            
            if not extension:
                return {'valid': False, 'errors': ['File has no extension']}
            
            if extension not in self.allowed_extensions:
                return {
                    'valid': False, 
                    'errors': [f'File extension {extension} is not allowed. Allowed: {self.allowed_extensions}']
                }
            
            return {'valid': True, 'errors': []}
            
        except Exception as e:
            return {'valid': False, 'errors': [f'Could not validate extension: {e}']}
    
    def _validate_mime_type(self, file_path: str) -> Dict[str, Any]:
        """Validate MIME type using python-magic or fallback to extension"""
        try:
            # Try to get MIME type using magic if available
            if MAGIC_AVAILABLE and magic:
                try:
                    mime_type = magic.from_file(file_path, mime=True)
                except Exception:
                    # Fallback to file extension if magic fails
                    extension = os.path.splitext(file_path)[1].lower()
                    mime_type = self._get_mime_type_from_extension(extension)
            else:
                # Fallback to file extension if magic is not available
                extension = os.path.splitext(file_path)[1].lower()
                mime_type = self._get_mime_type_from_extension(extension)
            
            if mime_type not in self.allowed_mime_types:
                return {
                    'valid': False,
                    'errors': [f'MIME type {mime_type} is not allowed. Allowed: {self.allowed_mime_types}']
                }
            
            return {'valid': True, 'errors': []}
            
        except Exception as e:
            return {'valid': False, 'errors': [f'Could not validate MIME type: {e}']}
    
    def _perform_security_checks(self, file_path: str) -> Dict[str, Any]:
        """Perform security checks on the file"""
        security_checks = {
            'suspicious_content': False,
            'executable_content': False,
            'script_content': False,
            'compressed_content': False,
            'warnings': []
        }
        
        try:
            # Read first 1KB to check for suspicious content
            with open(file_path, 'rb') as file:
                header = file.read(1024)
            
            # Check for executable signatures
            executable_signatures = [
                b'\x4d\x5a',  # PE executable
                b'\x7f\x45\x4c\x46',  # ELF executable
                b'\xfe\xed\xfa',  # Mach-O executable
            ]
            
            for sig in executable_signatures:
                if header.startswith(sig):
                    security_checks['executable_content'] = True
                    security_checks['warnings'].append("File appears to be an executable")
                    break
            
            # Check for script content
            script_indicators = [b'#!/', b'<script', b'<?php', b'#!/bin/', b'#!/usr/bin/']
            for indicator in script_indicators:
                if indicator in header:
                    security_checks['script_content'] = True
                    security_checks['warnings'].append("File appears to contain script content")
                    break
            
            # Check for compressed content (ZIP, RAR, etc.)
            compressed_signatures = [
                b'PK\x03\x04',  # ZIP
                b'Rar!\x1a\x07',  # RAR
                b'\x1f\x8b',  # GZIP
            ]
            
            for sig in compressed_signatures:
                if header.startswith(sig):
                    security_checks['compressed_content'] = True
                    break
            
            # Overall suspicious content check
            if (security_checks['executable_content'] or 
                security_checks['script_content']):
                security_checks['suspicious_content'] = True
            
        except Exception as e:
            logger.error(f"Error during security checks: {e}")
            security_checks['warnings'].append(f"Could not perform security checks: {e}")
        
        return security_checks
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of the file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as file:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: file.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate file hash: {e}")
            return ""
    
    def _parse_allowed_types(self) -> List[str]:
        """Parse allowed file types from environment variable"""
        allowed_types = os.getenv('ALLOWED_FILE_TYPES', 
                                '.pdf,.jpg,.jpeg,.png,.gif,.mp4,.mp3,.zip,.txt,.doc,.docx')
        return [ext.strip().lower() for ext in allowed_types.split(',') if ext.strip()]
    
    def _get_allowed_mime_types(self) -> List[str]:
        """Get allowed MIME types based on allowed extensions"""
        mime_type_map = {
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
        
        allowed_mime_types = []
        for ext in self.allowed_extensions:
            if ext in mime_type_map:
                allowed_mime_types.append(mime_type_map[ext])
        
        return allowed_mime_types
    
    def _get_mime_type_from_extension(self, extension: str) -> str:
        """Get MIME type from file extension (fallback method)"""
        mime_type_map = {
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
        return mime_type_map.get(extension, 'application/octet-stream')
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Get a human-readable validation summary"""
        if validation_result['valid']:
            return "✅ File validation passed"
        else:
            errors = validation_result['errors']
            return f"❌ File validation failed: {', '.join(errors)}"
