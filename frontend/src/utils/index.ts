import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Utility function to merge Tailwind classes
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// File utilities
export const FileUtils = {
  formatSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  getFileIcon: (filename: string): string => {
    const extension = filename.split('.').pop()?.toLowerCase();
    const iconMap: Record<string, string> = {
      pdf: 'file-text',
      jpg: 'image',
      jpeg: 'image',
      png: 'image',
      gif: 'image',
      mp4: 'video',
      mp3: 'music',
      zip: 'archive',
      txt: 'file-text',
      doc: 'file-text',
      docx: 'file-text',
    };
    return iconMap[extension || ''] || 'file';
  },

  validateFile: (file: File): { valid: boolean; errors: string[] } => {
    const errors: string[] = [];
    const maxSize = 100 * 1024 * 1024; // 100MB
    const allowedTypes = [
      'application/pdf',
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/gif',
      'video/mp4',
      'audio/mpeg',
      'application/zip',
      'text/plain',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];

    if (file.size > maxSize) {
      errors.push(`File size exceeds maximum allowed size of ${FileUtils.formatSize(maxSize)}`);
    }

    if (!allowedTypes.includes(file.type)) {
      errors.push('File type not allowed');
    }

    if (file.name.length > 255) {
      errors.push('Filename too long');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  },

  generateUniqueId: (): string => {
    return Math.random().toString(36).substr(2, 9);
  },
};

// Date utilities
export const DateUtils = {
  formatTimestamp: (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  },

  timeAgo: (timestamp: string): string => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
  },
};

// Local storage utilities
export const Storage = {
  get: <T>(key: string, defaultValue: T): T => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch {
      return defaultValue;
    }
  },

  set: <T>(key: string, value: T): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  },

  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
    }
  },
};

// API utilities
export const ApiUtils = {
  getApiBaseUrl: (): string => {
    return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  },

  handleApiError: (error: any): string => {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  },
};

// Permission utilities
export const PermissionUtils = {
  hasPermission: (userRole: string, requiredPermission: string): boolean => {
    const rolePermissions: Record<string, string[]> = {
      admin: ['upload', 'view', 'admin', 'delete'],
      uploader: ['upload', 'view'],
      viewer: ['view'],
    };

    return rolePermissions[userRole]?.includes(requiredPermission) || false;
  },

  canUpload: (userRole: string): boolean => {
    return PermissionUtils.hasPermission(userRole, 'upload');
  },

  canView: (userRole: string): boolean => {
    return PermissionUtils.hasPermission(userRole, 'view');
  },

  canAdmin: (userRole: string): boolean => {
    return PermissionUtils.hasPermission(userRole, 'admin');
  },

  canDelete: (userRole: string): boolean => {
    return PermissionUtils.hasPermission(userRole, 'delete');
  },
};
