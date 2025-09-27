import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { LoginForm } from "./LoginForm";
import { RegisterForm } from "./RegisterForm";
import { ConfirmForm } from "./ConfirmForm";
import { useAuthContext } from "@/contexts/AuthContext";
import { LoginFormData, RegisterFormData, ConfirmFormData } from "@/types";

type AuthView = "login" | "register" | "confirm";

export const AuthContainer: React.FC = () => {
	const [currentView, setCurrentView] = useState<AuthView>("login");
	const [isLoading, setIsLoading] = useState(false);
	const { login, register, confirmUser } = useAuthContext();
	const location = useLocation();
	const navigate = useNavigate();

	// Set current view based on the current route
	useEffect(() => {
		const path = location.pathname;
		if (path === "/register") {
			setCurrentView("register");
		} else if (path === "/confirm") {
			setCurrentView("confirm");
		} else {
			setCurrentView("login");
		}
	}, [location.pathname]);

	const handleLogin = async (data: LoginFormData) => {
		setIsLoading(true);
		try {
			await login(data);
		} finally {
			setIsLoading(false);
		}
	};

	const handleRegister = async (data: RegisterFormData) => {
		setIsLoading(true);
		try {
			await register(data);
			navigate("/confirm");
		} finally {
			setIsLoading(false);
		}
	};

	const handleConfirm = async (data: ConfirmFormData) => {
		setIsLoading(true);
		try {
			await confirmUser(data);
			navigate("/login");
		} finally {
			setIsLoading(false);
		}
	};

	const switchToLogin = () => navigate("/login");
	const switchToRegister = () => navigate("/register");

	return (
		<div className="min-h-screen bg-gradient-to-br from-aws-dark-blue via-aws-squid-ink to-aws-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
			<div className="max-w-md w-full space-y-8">
				<div className="bg-white rounded-2xl shadow-2xl p-8">
					{currentView === "login" && (
						<LoginForm
							onSubmit={handleLogin}
							onSwitchToRegister={switchToRegister}
							isLoading={isLoading}
						/>
					)}
					{currentView === "register" && (
						<RegisterForm
							onSubmit={handleRegister}
							onSwitchToLogin={switchToLogin}
							isLoading={isLoading}
						/>
					)}
					{currentView === "confirm" && (
						<ConfirmForm
							onSubmit={handleConfirm}
							onSwitchToLogin={switchToLogin}
							isLoading={isLoading}
						/>
					)}
				</div>
			</div>
		</div>
	);
};
