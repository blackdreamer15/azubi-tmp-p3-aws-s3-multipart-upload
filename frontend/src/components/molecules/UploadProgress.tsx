import React from "react";
import { ProgressBar } from "../atoms/ProgressBar";
import { Icon } from "../atoms/Icon";

interface UploadProgressProps {
	fileName: string;
	progress: number;
	status: "uploading" | "completed" | "error" | "paused";
	fileSize?: number;
	uploadedSize?: number;
	speed?: number; // bytes per second
	className?: string;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({
	fileName,
	progress,
	status,
	fileSize,
	uploadedSize,
	speed,
	className = "",
}) => {
	const getStatusIcon = () => {
		switch (status) {
			case "completed":
				return <Icon name="check" className="text-green-600" />;
			case "error":
				return <Icon name="error" className="text-red-600" />;
			case "paused":
				return <Icon name="warning" className="text-yellow-600" />;
			default:
				return <Icon name="upload" className="text-blue-600" />;
		}
	};

	const getStatusColor = () => {
		switch (status) {
			case "completed":
				return "success";
			case "error":
				return "danger";
			case "paused":
				return "warning";
			default:
				return "default";
		}
	};

	const formatBytes = (bytes: number) => {
		if (bytes === 0) return "0 Bytes";
		const k = 1024;
		const sizes = ["Bytes", "KB", "MB", "GB"];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
	};

	const formatSpeed = (bytesPerSecond: number) => {
		return formatBytes(bytesPerSecond) + "/s";
	};

	return (
		<div
			className={`bg-white p-4 rounded-lg border border-gray-200 ${className}`}
		>
			<div className="flex items-center justify-between mb-2">
				<div className="flex items-center space-x-2">
					{getStatusIcon()}
					<span className="font-medium text-gray-900 truncate">{fileName}</span>
				</div>
				<span className="text-sm text-gray-500 capitalize">{status}</span>
			</div>

			<ProgressBar
				progress={progress}
				variant={getStatusColor() as any}
				size="md"
				showPercentage={true}
				className="mb-2"
			/>

			<div className="flex justify-between text-sm text-gray-600">
				<div>
					{fileSize && uploadedSize && (
						<span>
							{formatBytes(uploadedSize)} / {formatBytes(fileSize)}
						</span>
					)}
				</div>
				<div>
					{speed && status === "uploading" && <span>{formatSpeed(speed)}</span>}
				</div>
			</div>
		</div>
	);
};
