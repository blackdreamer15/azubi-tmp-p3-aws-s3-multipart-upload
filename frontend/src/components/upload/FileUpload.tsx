import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X, File } from "lucide-react";
import { FileUpload as FileUploadType } from "@/types";
import { FileUtils, cn } from "@/utils";

interface FileUploadProps {
	onFilesSelected: (files: FileUploadType[]) => void;
	disabled?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
	onFilesSelected,
	disabled = false,
}) => {
	const [selectedFiles, setSelectedFiles] = useState<FileUploadType[]>([]);

	const onDrop = useCallback(
		(acceptedFiles: File[]) => {
			const validFiles: FileUploadType[] = [];
			const errors: string[] = [];

			acceptedFiles.forEach((file) => {
				const validation = FileUtils.validateFile(file);
				if (validation.valid) {
					const fileUpload: FileUploadType = {
						id: FileUtils.generateUniqueId(),
						file,
						name: file.name,
						size: file.size,
						type: file.type,
						status: "selected",
						progress: 0,
						parts: [],
					};
					validFiles.push(fileUpload);
				} else {
					errors.push(`${file.name}: ${validation.errors.join(", ")}`);
				}
			});

			if (validFiles.length > 0) {
				const newFiles = [...selectedFiles, ...validFiles];
				setSelectedFiles(newFiles);
				onFilesSelected(newFiles);
			}

			if (errors.length > 0) {
				errors.forEach((error) => {
					console.error(error);
				});
			}
		},
		[selectedFiles, onFilesSelected]
	);

	const { getRootProps, getInputProps, isDragActive } = useDropzone({
		onDrop,
		disabled,
		multiple: true,
		accept: {
			"application/pdf": [".pdf"],
			"image/*": [".jpg", ".jpeg", ".png", ".gif"],
			"video/mp4": [".mp4"],
			"audio/mpeg": [".mp3"],
			"application/zip": [".zip"],
			"text/plain": [".txt"],
			"application/msword": [".doc"],
			"application/vnd.openxmlformats-officedocument.wordprocessingml.document":
				[".docx"],
		},
	});

	const removeFile = (fileId: string) => {
		const newFiles = selectedFiles.filter((file) => file.id !== fileId);
		setSelectedFiles(newFiles);
		onFilesSelected(newFiles);
	};

	const clearAllFiles = () => {
		setSelectedFiles([]);
		onFilesSelected([]);
	};

	return (
		<div className="space-y-6">
			{/* Drop Zone */}
			<div
				{...getRootProps()}
				className={cn(
					"border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
					isDragActive
						? "border-aws-light-blue bg-blue-50"
						: "border-gray-300 hover:border-gray-400",
					disabled && "opacity-50 cursor-not-allowed"
				)}
			>
				<input {...getInputProps()} />
				<Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
				{isDragActive ? (
					<p className="text-lg font-medium text-aws-light-blue">
						Drop the files here...
					</p>
				) : (
					<div>
						<p className="text-lg font-medium text-gray-900 mb-2">
							Drag and drop files here, or click to select
						</p>
						<p className="text-sm text-gray-500">
							Maximum file size: 100MB per file
						</p>
						<p className="text-sm text-gray-500">
							Supported: PDF, Images, Videos, Audio, Documents, Archives
						</p>
					</div>
				)}
			</div>

			{/* Selected Files */}
			{selectedFiles.length > 0 && (
				<div className="space-y-4">
					<div className="flex items-center justify-between">
						<h3 className="text-lg font-medium text-gray-900">
							Selected Files ({selectedFiles.length})
						</h3>
						<button
							onClick={clearAllFiles}
							className="text-sm text-red-600 hover:text-red-700 font-medium"
						>
							Clear All
						</button>
					</div>

					<div className="space-y-2">
						{selectedFiles.map((file) => (
							<div
								key={file.id}
								className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
							>
								<div className="flex items-center space-x-3">
									<File className="h-5 w-5 text-gray-400" />
									<div>
										<p className="text-sm font-medium text-gray-900">
											{file.name}
										</p>
										<p className="text-xs text-gray-500">
											{FileUtils.formatSize(file.size)}
										</p>
									</div>
								</div>
								<button
									onClick={() => removeFile(file.id)}
									className="text-gray-400 hover:text-red-500 transition-colors"
									title="Remove file"
									aria-label="Remove file"
								>
									<X className="h-4 w-4" />
								</button>
							</div>
						))}
					</div>
				</div>
			)}
		</div>
	);
};
