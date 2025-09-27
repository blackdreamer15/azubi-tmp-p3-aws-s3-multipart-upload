import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
	User,
	LoginFormData,
	RegisterFormData,
	ConfirmFormData,
} from "@/types";
import { authService } from "@/services/authService";
import toast from "react-hot-toast";

interface UseAuthReturn {
	user: User | null;
	isAuthenticated: boolean;
	isLoading: boolean;
	login: (data: LoginFormData) => Promise<void>;
	register: (data: RegisterFormData) => Promise<void>;
	confirmUser: (data: ConfirmFormData) => Promise<void>;
	logout: () => Promise<void>;
	hasPermission: (permission: string) => boolean;
}

export const useAuth = (): UseAuthReturn => {
	const [user, setUser] = useState<User | null>(null);
	const [isAuthenticated, setIsAuthenticated] = useState(false);
	const [isLoading, setIsLoading] = useState(true);
	const navigate = useNavigate();

	// Initialize auth state
	useEffect(() => {
		const initAuth = async () => {
			try {
				console.log("Initializing auth...");
				if (authService.isAuthenticated()) {
					console.log(
						"User appears to be authenticated, loading stored data..."
					);
					const storedUser = authService.getUser();
					if (storedUser) {
						console.log("Found stored user:", storedUser.email);
						setUser(storedUser);
						setIsAuthenticated(true);

						// Only validate token if it's close to expiry (within 5 minutes)
						const tokens = authService.getTokens();
						if (tokens?.expires_at) {
							const timeUntilExpiry = tokens.expires_at - Date.now();
							const fiveMinutes = 5 * 60 * 1000; // 5 minutes in milliseconds

							if (timeUntilExpiry < fiveMinutes) {
								console.log("Token expires soon, attempting refresh...");
								try {
									const newTokens = await authService.refreshToken();
									authService.setTokens(newTokens);
									console.log("Token refreshed successfully");
								} catch (refreshError) {
									console.log("Token refresh failed, clearing auth state...");
									authService.logout();
									setUser(null);
									setIsAuthenticated(false);
								}
							} else {
								console.log("Token is still valid, no need to refresh");
							}
						}
					} else {
						console.log("No stored user found, clearing auth state");
						// No stored user, clear auth state
						authService.logout();
						setUser(null);
						setIsAuthenticated(false);
					}
				} else {
					console.log("User not authenticated, ensuring clean state");
					// Not authenticated, ensure clean state
					setUser(null);
					setIsAuthenticated(false);
				}
			} catch (error) {
				console.error("Auth initialization failed:", error);
				// Clear auth state on any error
				authService.logout();
				setUser(null);
				setIsAuthenticated(false);
			} finally {
				setIsLoading(false);
			}
		};

		initAuth();
	}, []);

	const handleLogout = useCallback(async () => {
		await authService.logout();
		setUser(null);
		setIsAuthenticated(false);
		toast.success("Logged out successfully");
		navigate("/login", { replace: true });
	}, [navigate]);

	const login = useCallback(
		async (data: LoginFormData): Promise<void> => {
			try {
				const result = await authService.login(data);

				const tokens = {
					access_token: result.access_token!,
					id_token: result.id_token!,
					refresh_token: result.refresh_token!,
					token_type: result.token_type!,
					expires_in: result.expires_in!,
				};

				authService.setTokens(tokens);
				authService.setUser(result.user!);

				setUser(result.user!);
				setIsAuthenticated(true);

				toast.success("Login successful!");
				navigate("/dashboard");
			} catch (error) {
				toast.error(error instanceof Error ? error.message : "Login failed");
				throw error;
			}
		},
		[navigate]
	);

	const register = useCallback(
		async (data: RegisterFormData): Promise<void> => {
			try {
				await authService.register(data);
				toast.success(
					"Registration successful! Please check your email for confirmation."
				);
			} catch (error) {
				toast.error(
					error instanceof Error ? error.message : "Registration failed"
				);
				throw error;
			}
		},
		[]
	);

	const confirmUser = useCallback(
		async (data: ConfirmFormData): Promise<void> => {
			try {
				await authService.confirmUser(data);
				toast.success("Account confirmed successfully! You can now login.");
			} catch (error) {
				toast.error(
					error instanceof Error ? error.message : "Confirmation failed"
				);
				throw error;
			}
		},
		[]
	);

	const logout = useCallback(async (): Promise<void> => {
		await handleLogout();
	}, [handleLogout]);

	const hasPermission = useCallback((permission: string): boolean => {
		return authService.hasPermission(permission);
	}, []);

	return {
		user,
		isAuthenticated,
		isLoading,
		login,
		register,
		confirmUser,
		logout,
		hasPermission,
	};
};
