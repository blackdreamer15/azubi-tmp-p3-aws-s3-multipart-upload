import { useState, useCallback } from "react";
import { FileUpload } from "@/types";
import { uploadService } from "@/services/uploadService";
import toast from "react-hot-toast";

interface UseUploadReturn {
	uploads: FileUpload[];
	isUploading: boolean;
	uploadFiles: (files: FileUpload[]) => Promise<void>;
	updateUploadProgress: (fileId: string, progress: number) => void;
	updateUploadStatus: (
		fileId: string,
		status: FileUpload["status"],
		error?: string
	) => void;
	clearUploads: () => void;
}

export const useUpload = (): UseUploadReturn => {
	const [uploads, setUploads] = useState<FileUpload[]>([]);
	const [isUploading, setIsUploading] = useState(false);

	const updateUploadProgress = useCallback(
		(fileId: string, progress: number) => {
			setUploads((prev) =>
				prev.map((upload) =>
					upload.id === fileId
						? { ...upload, progress: Math.round(progress) }
						: upload
				)
			);
		},
		[]
	);

	const updateUploadStatus = useCallback(
		(fileId: string, status: FileUpload["status"], error?: string) => {
			setUploads((prev) =>
				prev.map((upload) =>
					upload.id === fileId ? { ...upload, status, error } : upload
				)
			);
		},
		[]
	);

	const uploadFiles = useCallback(
		async (files: FileUpload[]): Promise<void> => {
			if (files.length === 0) {
				toast.error("No files selected for upload");
				return;
			}

			setIsUploading(true);

			// Initialize uploads with selected status
			setUploads(
				files.map((file) => ({
					...file,
					status: "selected" as const,
					progress: 0,
				}))
			);

			const uploadPromises = files.map(async (fileUpload) => {
				try {
					// Update status to uploading
					updateUploadStatus(fileUpload.id, "uploading");

					// Upload the file
					const result = await uploadService.uploadFile(
						fileUpload.file,
						(progress) => updateUploadProgress(fileUpload.id, progress),
						{
							userId: "current-user", // You can get this from auth context
							uploadedAt: new Date().toISOString(),
						}
					);

					// Update status to completed
					updateUploadStatus(fileUpload.id, "completed");

					toast.success(`${fileUpload.file.name} uploaded successfully!`);

					return result;
				} catch (error) {
					const errorMessage =
						error instanceof Error ? error.message : "Upload failed";
					updateUploadStatus(fileUpload.id, "error", errorMessage);
					toast.error(`${fileUpload.file.name}: ${errorMessage}`);
					throw error;
				}
			});

			try {
				await Promise.all(uploadPromises);
				toast.success("All files uploaded successfully!");
			} catch (error) {
				console.error("Some uploads failed:", error);
			} finally {
				setIsUploading(false);
			}
		},
		[updateUploadStatus, updateUploadProgress]
	);

	const clearUploads = useCallback(() => {
		setUploads([]);
	}, []);

	return {
		uploads,
		isUploading,
		uploadFiles,
		updateUploadProgress,
		updateUploadStatus,
		clearUploads,
	};
};
