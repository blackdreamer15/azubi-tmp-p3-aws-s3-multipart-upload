import React from "react";

interface ProgressBarProps {
	progress: number; // 0-100
	size?: "sm" | "md" | "lg";
	variant?: "default" | "success" | "warning" | "danger";
	showPercentage?: boolean;
	className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
	progress,
	size = "md",
	variant = "default",
	showPercentage = true,
	className = "",
}) => {
	const sizeClasses = {
		sm: "h-2",
		md: "h-3",
		lg: "h-4",
	};

	const variantClasses = {
		default: "bg-blue-600",
		success: "bg-green-600",
		warning: "bg-yellow-600",
		danger: "bg-red-600",
	};

	const baseClasses = "w-full bg-gray-200 rounded-full overflow-hidden";
	const progressClasses = `transition-all duration-300 ease-out ${variantClasses[variant]}`;

	const classes = `${baseClasses} ${sizeClasses[size]} ${className}`;

	return (
		<div className="w-full">
			<div className={classes}>
				<div
					className={`${progressClasses} ${sizeClasses[size]} rounded-full`}
					style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
				/>
			</div>
			{showPercentage && (
				<div className="mt-1 text-sm text-gray-600 text-center">
					{Math.round(progress)}%
				</div>
			)}
		</div>
	);
};
