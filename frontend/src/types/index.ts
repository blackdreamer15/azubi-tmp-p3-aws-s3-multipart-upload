// Authentication Types
export interface User {
	user_id: string;
	email: string;
	name: string;
	role: "admin" | "uploader" | "viewer";
	groups: string[];
	status: string;
}

export interface AuthTokens {
	access_token: string;
	id_token: string;
	refresh_token: string;
	token_type: string;
	expires_in: number;
	expires_at?: number; // Added for easier expiry checking
}

export interface AuthResponse {
	success: boolean;
	message: string;
	access_token?: string;
	id_token?: string;
	refresh_token?: string;
	token_type?: string;
	expires_in?: number;
	user?: User;
}

// Upload Types
export interface FileUpload {
	id: string;
	file: File;
	name: string;
	size: number;
	type: string;
	status:
		| "selected"
		| "initializing"
		| "uploading"
		| "completing"
		| "completed"
		| "error";
	progress: number;
	uploadId?: string;
	parts: UploadPart[];
	error?: string;
	url?: string;
}

export interface UploadPart {
	part_number: number;
	etag: string;
}

export interface InitiateUploadRequest {
	file_key: string;
	file_size: number;
	content_type: string;
	metadata?: Record<string, string>;
}

export interface InitiateUploadResponse {
	upload_id: string;
	file_key: string;
	message: string;
}

export interface PresignedUrlRequest {
	file_key: string;
	upload_id: string;
	part_number: number;
	expiration?: number;
}

export interface PresignedUrlResponse {
	presigned_url: string;
	part_number: number;
	expires_in: number;
}

export interface CompleteUploadRequest {
	upload_id: string;
	file_key: string;
	parts: UploadPart[];
}

export interface CompleteUploadResponse {
	success: boolean;
	file_key: string;
	file_url: string;
	message: string;
}

// Security Types
export interface SecurityLog {
	timestamp: string;
	event_type: string;
	user_id: string;
	file_key?: string;
	file_size?: number;
	upload_status?: string;
	action?: string;
	resource?: string;
	success?: boolean;
	ip_address?: string;
	metadata?: Record<string, any>;
}

export interface SecurityLogResponse {
	logs: SecurityLog[];
	total_entries: number;
	query_timestamp: string;
}

// Configuration Types
export interface AppConfig {
	apiEndpoint: string;
	bucketName: string;
	connected: boolean;
}

// Form Types
export interface LoginFormData {
	email: string;
	password: string;
}

export interface RegisterFormData {
	name: string;
	email: string;
	password: string;
	confirmPassword: string;
	role: "admin" | "uploader" | "viewer";
}

export interface ConfirmFormData {
	email: string;
	confirmation_code: string;
}

// API Response Types
export interface ApiResponse<T = any> {
	success: boolean;
	message: string;
	data?: T;
	error?: string;
}

// Health Check Types
export interface HealthResponse {
	status: string;
	message: string;
	timestamp: string;
	services: Record<string, string>;
}

// Bucket Test Types
export interface BucketTestRequest {
	bucket_name: string;
}

export interface BucketTestResponse {
	accessible: boolean;
	message: string;
	bucket_name: string;
}
