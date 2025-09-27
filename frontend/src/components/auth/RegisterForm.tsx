import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { Eye, EyeOff, UserPlus, Loader2 } from "lucide-react";
import { RegisterFormData } from "@/types";
import { cn } from "@/utils";

interface RegisterFormProps {
	onSubmit: (data: RegisterFormData) => Promise<void>;
	onSwitchToLogin: () => void;
	isLoading?: boolean;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({
	onSubmit,
	onSwitchToLogin,
	isLoading = false,
}) => {
	const [showPassword, setShowPassword] = useState(false);
	const [showConfirmPassword, setShowConfirmPassword] = useState(false);
	const {
		register,
		handleSubmit,
		watch,
		formState: { errors },
	} = useForm<RegisterFormData>();

	const password = watch("password");

	const handleFormSubmit = async (data: RegisterFormData) => {
		try {
			await onSubmit(data);
		} catch (error) {
			// Error handling is done in the hook
		}
	};

	return (
		<div className="w-full max-w-md mx-auto">
			<div className="text-center mb-8">
				<h2 className="text-3xl font-bold text-gray-900 mb-2">
					Create Account
				</h2>
				<p className="text-gray-600">
					Sign up to start uploading files securely
				</p>
			</div>

			<form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
				<div>
					<label
						htmlFor="name"
						className="block text-sm font-medium text-gray-700 mb-2"
					>
						Full Name
					</label>
					<input
						{...register("name", {
							required: "Full name is required",
							minLength: {
								value: 2,
								message: "Name must be at least 2 characters",
							},
						})}
						type="text"
						id="name"
						className={cn(
							"w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-aws-light-blue focus:border-transparent transition-colors",
							errors.name ? "border-red-500" : "border-gray-300"
						)}
						placeholder="Enter your full name"
						disabled={isLoading}
					/>
					{errors.name && (
						<p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
					)}
				</div>

				<div>
					<label
						htmlFor="email"
						className="block text-sm font-medium text-gray-700 mb-2"
					>
						Email Address
					</label>
					<input
						{...register("email", {
							required: "Email is required",
							pattern: {
								value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
								message: "Invalid email address",
							},
						})}
						type="email"
						id="email"
						className={cn(
							"w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-aws-light-blue focus:border-transparent transition-colors",
							errors.email ? "border-red-500" : "border-gray-300"
						)}
						placeholder="Enter your email"
						disabled={isLoading}
					/>
					{errors.email && (
						<p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
					)}
				</div>

				<div>
					<label
						htmlFor="role"
						className="block text-sm font-medium text-gray-700 mb-2"
					>
						Role
					</label>
					<select
						{...register("role", { required: "Role is required" })}
						id="role"
						className={cn(
							"w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-aws-light-blue focus:border-transparent transition-colors",
							errors.role ? "border-red-500" : "border-gray-300"
						)}
						disabled={isLoading}
					>
						<option value="uploader">Uploader</option>
						<option value="viewer">Viewer</option>
					</select>
					{errors.role && (
						<p className="mt-1 text-sm text-red-600">{errors.role.message}</p>
					)}
				</div>

				<div>
					<label
						htmlFor="password"
						className="block text-sm font-medium text-gray-700 mb-2"
					>
						Password
					</label>
					<div className="relative">
						<input
							{...register("password", {
								required: "Password is required",
								minLength: {
									value: 8,
									message: "Password must be at least 8 characters",
								},
								pattern: {
									value:
										/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
									message:
										"Password must contain uppercase, lowercase, number, and special character",
								},
							})}
							type={showPassword ? "text" : "password"}
							id="password"
							className={cn(
								"w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-aws-light-blue focus:border-transparent transition-colors",
								errors.password ? "border-red-500" : "border-gray-300"
							)}
							placeholder="Create a strong password"
							disabled={isLoading}
						/>
						<button
							type="button"
							className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
							onClick={() => setShowPassword(!showPassword)}
							disabled={isLoading}
						>
							{showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
						</button>
					</div>
					{errors.password && (
						<p className="mt-1 text-sm text-red-600">
							{errors.password.message}
						</p>
					)}
				</div>

				<div>
					<label
						htmlFor="confirmPassword"
						className="block text-sm font-medium text-gray-700 mb-2"
					>
						Confirm Password
					</label>
					<div className="relative">
						<input
							{...register("confirmPassword", {
								required: "Please confirm your password",
								validate: (value) =>
									value === password || "Passwords do not match",
							})}
							type={showConfirmPassword ? "text" : "password"}
							id="confirmPassword"
							className={cn(
								"w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-aws-light-blue focus:border-transparent transition-colors",
								errors.confirmPassword ? "border-red-500" : "border-gray-300"
							)}
							placeholder="Confirm your password"
							disabled={isLoading}
						/>
						<button
							type="button"
							className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
							onClick={() => setShowConfirmPassword(!showConfirmPassword)}
							disabled={isLoading}
						>
							{showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
						</button>
					</div>
					{errors.confirmPassword && (
						<p className="mt-1 text-sm text-red-600">
							{errors.confirmPassword.message}
						</p>
					)}
				</div>

				<button
					type="submit"
					disabled={isLoading}
					className={cn(
						"w-full flex items-center justify-center px-4 py-3 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-aws-light-blue hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aws-light-blue transition-colors",
						isLoading && "opacity-50 cursor-not-allowed"
					)}
				>
					{isLoading ? (
						<>
							<Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5" />
							Creating account...
						</>
					) : (
						<>
							<UserPlus className="-ml-1 mr-3 h-5 w-5" />
							Create Account
						</>
					)}
				</button>
			</form>

			<div className="mt-6 text-center">
				<p className="text-sm text-gray-600">
					Already have an account?{" "}
					<button
						type="button"
						onClick={onSwitchToLogin}
						className="font-medium text-aws-light-blue hover:text-blue-600 transition-colors"
						disabled={isLoading}
					>
						Sign in here
					</button>
				</p>
			</div>
		</div>
	);
};
