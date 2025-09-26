import {
	InitiateUploadRequest,
	InitiateUploadResponse,
	PresignedUrlRequest,
	PresignedUrlResponse,
	CompleteUploadRequest,
	CompleteUploadResponse,
} from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

class UploadService {
	private static instance: UploadService;

	static getInstance(): UploadService {
		if (!UploadService.instance) {
			UploadService.instance = new UploadService();
		}
		return UploadService.instance;
	}

	private getAuthHeaders(): HeadersInit {
		// Get tokens from localStorage directly to avoid circular dependency
		let tokens = null;
		try {
			const tokensData = localStorage.getItem("authTokens");
			tokens = tokensData ? JSON.parse(tokensData) : null;
		} catch (error) {
			console.error("Failed to get tokens from localStorage:", error);
		}

		if (!tokens?.access_token) {
			throw new Error("No access token available");
		}

		console.log(
			"🔑 Using access token:",
			tokens.access_token.substring(0, 50) + "..."
		);
		console.log(
			"🔑 Token expires at:",
			new Date(tokens.expires_at).toISOString()
		);

		return {
			Authorization: `Bearer ${tokens.access_token}`,
			"Content-Type": "application/json",
		};
	}

	async initiateUpload(
		file: File,
		metadata?: { [key: string]: string }
	): Promise<InitiateUploadResponse> {
		const fileKey = `uploads/${Date.now()}-${file.name}`;

		const request: InitiateUploadRequest = {
			file_key: fileKey,
			file_size: file.size,
			content_type: file.type,
			metadata: {
				originalName: file.name,
				uploadedAt: new Date().toISOString(),
				...metadata,
			},
		};

		const response = await fetch(`${API_BASE_URL}/api/upload/initiate`, {
			method: "POST",
			headers: this.getAuthHeaders(),
			body: JSON.stringify(request),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.message || "Failed to initiate upload");
		}

		return response.json();
	}

	async getPresignedUrl(
		fileKey: string,
		uploadId: string,
		partNumber: number
	): Promise<PresignedUrlResponse> {
		const request: PresignedUrlRequest = {
			file_key: fileKey,
			upload_id: uploadId,
			part_number: partNumber,
		};

		const response = await fetch(`${API_BASE_URL}/api/upload/presigned-url`, {
			method: "POST",
			headers: this.getAuthHeaders(),
			body: JSON.stringify(request),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.message || "Failed to get presigned URL");
		}

		return response.json();
	}

	async uploadPart(
		file: File,
		presignedUrl: string,
		partNumber: number,
		onProgress?: (progress: number) => void
	): Promise<string> {
		return new Promise((resolve, reject) => {
			const xhr = new XMLHttpRequest();

			// Calculate the part size (5MB chunks)
			const chunkSize = 5 * 1024 * 1024; // 5MB
			const start = (partNumber - 1) * chunkSize;
			const end = Math.min(start + chunkSize, file.size);
			const chunk = file.slice(start, end);

			xhr.upload.addEventListener("progress", (event) => {
				if (event.lengthComputable && onProgress) {
					const progress = (event.loaded / event.total) * 100;
					onProgress(progress);
				}
			});

			xhr.addEventListener("load", () => {
				if (xhr.status >= 200 && xhr.status < 300) {
					const etag = xhr.getResponseHeader("ETag");
					if (etag) {
						resolve(etag.replace(/"/g, "")); // Remove quotes from ETag
					} else {
						reject(new Error("No ETag received from server"));
					}
				} else {
					reject(new Error(`Upload failed with status: ${xhr.status}`));
				}
			});

			xhr.addEventListener("error", () => {
				reject(new Error("Upload failed"));
			});

			xhr.open("PUT", presignedUrl);
			// Don't set Content-Type for multipart uploads - let S3 handle it
			// xhr.setRequestHeader("Content-Type", file.type);
			xhr.send(chunk);
		});
	}

	async completeUpload(
		fileKey: string,
		uploadId: string,
		parts: { part_number: number; etag: string }[]
	): Promise<CompleteUploadResponse> {
		const request: CompleteUploadRequest = {
			upload_id: uploadId,
			file_key: fileKey,
			parts,
		};

		const response = await fetch(`${API_BASE_URL}/api/upload/complete`, {
			method: "POST",
			headers: this.getAuthHeaders(),
			body: JSON.stringify(request),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.message || "Failed to complete upload");
		}

		return response.json();
	}

	async uploadFile(
		file: File,
		onProgress?: (progress: number) => void,
		metadata?: { [key: string]: string }
	): Promise<CompleteUploadResponse> {
		try {
			// Step 1: Initiate upload
			const initiateResponse = await this.initiateUpload(file, metadata);
			const { upload_id: uploadId, file_key: fileKey } = initiateResponse;

			// Step 2: Calculate number of parts needed
			const chunkSize = 5 * 1024 * 1024; // 5MB
			const totalParts = Math.ceil(file.size / chunkSize);
			const parts: { part_number: number; etag: string }[] = [];

			// Step 3: Upload each part
			for (let partNumber = 1; partNumber <= totalParts; partNumber++) {
				// Get presigned URL for this part
				const presignedResponse = await this.getPresignedUrl(
					fileKey,
					uploadId,
					partNumber
				);
				const { presigned_url: presignedUrl } = presignedResponse;

				// Upload the part
				const partProgress = (partNumber - 1) / totalParts;
				const etag = await this.uploadPart(
					file,
					presignedUrl,
					partNumber,
					(partProgressValue) => {
						if (onProgress) {
							const overallProgress =
								(partProgress + partProgressValue / 100 / totalParts) * 100;
							onProgress(overallProgress);
						}
					}
				);

				parts.push({ part_number: partNumber, etag });
			}

			// Step 4: Complete the upload
			const completeResponse = await this.completeUpload(
				fileKey,
				uploadId,
				parts
			);
			return completeResponse;
		} catch (error) {
			throw new Error(
				`Upload failed: ${
					error instanceof Error ? error.message : "Unknown error"
				}`
			);
		}
	}
}

export const uploadService = UploadService.getInstance();
