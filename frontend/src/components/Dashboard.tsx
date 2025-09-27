import React, { useState } from "react";
import {
	LogOut,
	User,
	Upload as UploadIcon,
	Shield,
	BarChart3,
	Loader2,
} from "lucide-react";
import { useAuthContext } from "@/contexts/AuthContext";
import { useUpload } from "@/hooks/useUpload";
import { FileUpload } from "@/components/upload/FileUpload";
import { FileUpload as FileUploadType } from "@/types";
import { cn } from "@/utils";

export const Dashboard: React.FC = () => {
	const { user, logout, hasPermission } = useAuthContext();
	const { uploads, isUploading, uploadFiles, clearUploads } = useUpload();
	const [selectedFiles, setSelectedFiles] = useState<FileUploadType[]>([]);
	const [activeTab, setActiveTab] = useState<"upload" | "history" | "security">(
		"upload"
	);

	const handleLogout = async () => {
		try {
			await logout();
		} catch (error) {
			console.error("Logout failed:", error);
		}
	};

	const handleFilesSelected = (files: FileUploadType[]) => {
		setSelectedFiles(files);
	};

	const handleStartUpload = async () => {
		if (selectedFiles.length === 0) {
			return;
		}

		try {
			await uploadFiles(selectedFiles);
			// Clear selected files after successful upload
			setSelectedFiles([]);
		} catch (error) {
			console.error("Upload failed:", error);
		}
	};

	const canUpload = hasPermission("upload");
	const canViewSecurity = hasPermission("admin");

	return (
		<div className="min-h-screen bg-gray-50">
			{/* Header */}
			<header className="bg-white shadow-sm border-b">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<div className="flex justify-between items-center h-16">
						<div className="flex items-center">
							<UploadIcon className="h-8 w-8 text-aws-light-blue mr-3" />
							<h1 className="text-xl font-semibold text-gray-900">
								Secure S3 Upload
							</h1>
						</div>

						<div className="flex items-center space-x-4">
							<div className="flex items-center space-x-2">
								<User className="h-5 w-5 text-gray-400" />
								<div className="text-sm">
									<p className="font-medium text-gray-900">{user?.name}</p>
									<p className="text-gray-500 capitalize">{user?.role}</p>
								</div>
							</div>
							<button
								onClick={handleLogout}
								className="flex items-center space-x-2 text-gray-500 hover:text-gray-700 transition-colors"
							>
								<LogOut className="h-5 w-5" />
								<span>Logout</span>
							</button>
						</div>
					</div>
				</div>
			</header>

			{/* Navigation Tabs */}
			<div className="bg-white border-b">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<nav className="flex space-x-8">
						<button
							onClick={() => setActiveTab("upload")}
							className={cn(
								"py-4 px-1 border-b-2 font-medium text-sm transition-colors",
								activeTab === "upload"
									? "border-aws-light-blue text-aws-light-blue"
									: "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
							)}
						>
							<UploadIcon className="h-4 w-4 inline mr-2" />
							Upload Files
						</button>
						<button
							onClick={() => setActiveTab("history")}
							className={cn(
								"py-4 px-1 border-b-2 font-medium text-sm transition-colors",
								activeTab === "history"
									? "border-aws-light-blue text-aws-light-blue"
									: "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
							)}
						>
							<BarChart3 className="h-4 w-4 inline mr-2" />
							Upload History
						</button>
						{canViewSecurity && (
							<button
								onClick={() => setActiveTab("security")}
								className={cn(
									"py-4 px-1 border-b-2 font-medium text-sm transition-colors",
									activeTab === "security"
										? "border-aws-light-blue text-aws-light-blue"
										: "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
								)}
							>
								<Shield className="h-4 w-4 inline mr-2" />
								Security
							</button>
						)}
					</nav>
				</div>
			</div>

			{/* Main Content */}
			<main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
				{activeTab === "upload" && (
					<div className="space-y-6">
						<div className="bg-white rounded-lg shadow p-6">
							<h2 className="text-lg font-medium text-gray-900 mb-4">
								Upload Files
							</h2>
							{canUpload ? (
								<FileUpload
									onFilesSelected={handleFilesSelected}
									disabled={false}
								/>
							) : (
								<div className="text-center py-12">
									<Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
									<h3 className="text-lg font-medium text-gray-900 mb-2">
										Upload Permission Required
									</h3>
									<p className="text-gray-500">
										You don't have permission to upload files. Contact your
										administrator.
									</p>
								</div>
							)}
						</div>

						{selectedFiles.length > 0 && canUpload && (
							<div className="bg-white rounded-lg shadow p-6">
								<h3 className="text-lg font-medium text-gray-900 mb-4">
									Ready to Upload ({selectedFiles.length} files)
								</h3>
								<button
									onClick={handleStartUpload}
									disabled={isUploading}
									className={cn(
										"w-full flex items-center justify-center py-3 px-4 rounded-lg font-medium transition-colors",
										isUploading
											? "bg-gray-400 cursor-not-allowed"
											: "bg-aws-light-blue text-white hover:bg-blue-600"
									)}
								>
									{isUploading ? (
										<>
											<Loader2 className="animate-spin h-5 w-5 mr-2" />
											Uploading...
										</>
									) : (
										<>
											<UploadIcon className="h-5 w-5 mr-2" />
											Start Upload
										</>
									)}
								</button>
							</div>
						)}

						{/* Upload Progress */}
						{uploads.length > 0 && (
							<div className="bg-white rounded-lg shadow p-6">
								<div className="flex items-center justify-between mb-4">
									<h3 className="text-lg font-medium text-gray-900">
										Upload Progress
									</h3>
									<button
										onClick={clearUploads}
										className="text-sm text-gray-500 hover:text-gray-700"
									>
										Clear
									</button>
								</div>
								<div className="space-y-3">
									{uploads.map((upload) => (
										<div key={upload.id} className="border rounded-lg p-3">
											<div className="flex items-center justify-between mb-2">
												<span className="text-sm font-medium text-gray-900">
													{upload.file.name}
												</span>
												<span
													className={cn(
														"text-xs px-2 py-1 rounded-full",
														upload.status === "completed" &&
															"bg-green-100 text-green-800",
														upload.status === "uploading" &&
															"bg-blue-100 text-blue-800",
														upload.status === "error" &&
															"bg-red-100 text-red-800",
														upload.status === "initializing" &&
															"bg-gray-100 text-gray-800"
													)}
												>
													{upload.status}
												</span>
											</div>
											{upload.status === "uploading" && (
												<div className="w-full bg-gray-200 rounded-full h-2">
													<div
														className="bg-aws-light-blue h-2 rounded-full transition-all duration-300"
														style={{ width: `${upload.progress}%` }}
													></div>
												</div>
											)}
											{upload.status === "error" && upload.error && (
												<p className="text-xs text-red-600 mt-1">
													{upload.error}
												</p>
											)}
										</div>
									))}
								</div>
							</div>
						)}
					</div>
				)}

				{activeTab === "history" && (
					<div className="bg-white rounded-lg shadow p-6">
						<h2 className="text-lg font-medium text-gray-900 mb-4">
							Upload History
						</h2>
						<div className="text-center py-12">
							<BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
							<h3 className="text-lg font-medium text-gray-900 mb-2">
								No upload history yet
							</h3>
							<p className="text-gray-500">
								Your file uploads will appear here once you start uploading.
							</p>
						</div>
					</div>
				)}

				{activeTab === "security" && canViewSecurity && (
					<div className="bg-white rounded-lg shadow p-6">
						<h2 className="text-lg font-medium text-gray-900 mb-4">
							Security Dashboard
						</h2>
						<div className="text-center py-12">
							<Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
							<h3 className="text-lg font-medium text-gray-900 mb-2">
								Security monitoring active
							</h3>
							<p className="text-gray-500">
								All uploads are encrypted and monitored for security.
							</p>
						</div>
					</div>
				)}
			</main>
		</div>
	);
};
