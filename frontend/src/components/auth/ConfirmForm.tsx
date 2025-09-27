import React from "react";
import { useForm } from "react-hook-form";
import { CheckCircle, Loader2, ArrowLeft } from "lucide-react";
import { ConfirmFormData } from "@/types";
import { cn } from "@/utils";

interface ConfirmFormProps {
	onSubmit: (data: ConfirmFormData) => Promise<void>;
	onSwitchToLogin: () => void;
	isLoading?: boolean;
}

export const ConfirmForm: React.FC<ConfirmFormProps> = ({
	onSubmit,
	onSwitchToLogin,
	isLoading = false,
}) => {
	const {
		register,
		handleSubmit,
		formState: { errors },
	} = useForm<ConfirmFormData>();

	const handleFormSubmit = async (data: ConfirmFormData) => {
		try {
			await onSubmit(data);
		} catch (error) {
			// Error handling is done in the hook
		}
	};

	return (
		<div className="w-full max-w-md mx-auto">
			<div className="text-center mb-8">
				<div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
					<CheckCircle className="h-6 w-6 text-green-600" />
				</div>
				<h2 className="text-3xl font-bold text-gray-900 mb-2">
					Confirm Your Account
				</h2>
				<p className="text-gray-600">
					We've sent a confirmation code to your email address. Please enter it
					below to activate your account.
				</p>
			</div>

			<form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
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
						placeholder="Enter your email address"
						disabled={isLoading}
					/>
					{errors.email && (
						<p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
					)}
				</div>

				<div>
					<label
						htmlFor="confirmation_code"
						className="block text-sm font-medium text-gray-700 mb-2"
					>
						Confirmation Code
					</label>
					<input
						{...register("confirmation_code", {
							required: "Confirmation code is required",
							minLength: {
								value: 6,
								message: "Confirmation code must be at least 6 characters",
							},
						})}
						type="text"
						id="confirmation_code"
						className={cn(
							"w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-aws-light-blue focus:border-transparent transition-colors text-center text-lg tracking-widest",
							errors.confirmation_code ? "border-red-500" : "border-gray-300"
						)}
						placeholder="Enter 6-digit code"
						maxLength={6}
						disabled={isLoading}
					/>
					{errors.confirmation_code && (
						<p className="mt-1 text-sm text-red-600">
							{errors.confirmation_code.message}
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
							Confirming...
						</>
					) : (
						<>
							<CheckCircle className="-ml-1 mr-3 h-5 w-5" />
							Confirm Account
						</>
					)}
				</button>
			</form>

			<div className="mt-6 text-center">
				<p className="text-sm text-gray-600">
					Didn't receive the code?{" "}
					<button
						type="button"
						className="font-medium text-aws-light-blue hover:text-blue-600 transition-colors"
						disabled={isLoading}
					>
						Resend code
					</button>
				</p>
				<button
					type="button"
					onClick={onSwitchToLogin}
					className="mt-4 flex items-center justify-center text-sm text-gray-500 hover:text-gray-700 transition-colors"
					disabled={isLoading}
				>
					<ArrowLeft className="h-4 w-4 mr-1" />
					Back to Sign In
				</button>
			</div>
		</div>
	);
};
