import {
	AuthTokens,
	User,
	LoginFormData,
	RegisterFormData,
	ConfirmFormData,
	AuthResponse,
} from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

class AuthService {
	private static instance: AuthService;

	static getInstance(): AuthService {
		if (!AuthService.instance) {
			AuthService.instance = new AuthService();
		}
		return AuthService.instance;
	}

	// Token management
	getTokens(): AuthTokens | null {
		try {
			const tokens = localStorage.getItem("authTokens");
			return tokens ? JSON.parse(tokens) : null;
		} catch {
			return null;
		}
	}

	setTokens(tokens: AuthTokens): void {
		// Extract expiry time from the JWT token itself
		let expiresAt = Date.now() + tokens.expires_in * 1000; // Fallback calculation

		try {
			// Decode the JWT to get the actual expiry time
			const payload = JSON.parse(atob(tokens.access_token.split(".")[1]));
			if (payload.exp) {
				expiresAt = payload.exp * 1000; // Convert from seconds to milliseconds
			}
		} catch (error) {
			console.warn(
				"Could not decode JWT token, using fallback expiry calculation"
			);
		}

		const tokensWithExpiry = {
			...tokens,
			expires_at: expiresAt,
		};
		localStorage.setItem("authTokens", JSON.stringify(tokensWithExpiry));
	}

	clearTokens(): void {
		localStorage.removeItem("authTokens");
	}

	// User management
	getUser(): User | null {
		try {
			const user = localStorage.getItem("user");
			return user ? JSON.parse(user) : null;
		} catch {
			return null;
		}
	}

	setUser(user: User): void {
		localStorage.setItem("user", JSON.stringify(user));
	}

	clearUser(): void {
		localStorage.removeItem("user");
	}

	// API calls
	async login(credentials: LoginFormData): Promise<AuthResponse> {
		const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(credentials),
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.message || "Login failed");
		}

		return data;
	}

	async register(userData: RegisterFormData): Promise<AuthResponse> {
		const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				email: userData.email,
				password: userData.password,
				name: userData.name,
				role: userData.role,
			}),
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.message || "Registration failed");
		}

		return data;
	}

	async confirmUser(confirmData: ConfirmFormData): Promise<AuthResponse> {
		const response = await fetch(`${API_BASE_URL}/api/auth/confirm`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(confirmData),
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.message || "Confirmation failed");
		}

		return data;
	}

	async getCurrentUser(): Promise<User> {
		const tokens = this.getTokens();
		if (!tokens?.access_token) {
			throw new Error("No access token available");
		}

		const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
			method: "GET",
			headers: {
				Authorization: `Bearer ${tokens.access_token}`,
				"Content-Type": "application/json",
			},
		});

		if (!response.ok) {
			if (response.status === 401 || response.status === 403) {
				throw new Error("Token expired or invalid");
			}
			throw new Error("Failed to get user info");
		}

		return response.json();
	}

	async refreshToken(): Promise<AuthTokens> {
		const tokens = this.getTokens();
		if (!tokens?.refresh_token) {
			throw new Error("No refresh token available");
		}

		const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ refresh_token: tokens.refresh_token }),
		});

		if (!response.ok) {
			throw new Error("Token refresh failed");
		}

		const data = await response.json();
		return {
			access_token: data.access_token!,
			id_token: data.id_token!,
			refresh_token: tokens.refresh_token, // Keep the same refresh token
			token_type: data.token_type!,
			expires_in: data.expires_in!,
		};
	}

	async logout(): Promise<void> {
		const tokens = this.getTokens();
		if (tokens?.access_token) {
			try {
				await fetch(`${API_BASE_URL}/api/auth/logout`, {
					method: "POST",
					headers: {
						Authorization: `Bearer ${tokens.access_token}`,
						"Content-Type": "application/json",
					},
				});
			} catch (error) {
				console.warn("Logout API call failed:", error);
			}
		}

		this.clearTokens();
		this.clearUser();
	}

	// Utility methods
	isAuthenticated(): boolean {
		const tokens = this.getTokens();
		const user = this.getUser();

		// Check if we have both tokens and user data
		if (!tokens?.access_token || !user) {
			return false;
		}

		// Check if token is expired (basic check)
		if (tokens.expires_at) {
			const now = Date.now();
			if (now >= tokens.expires_at) {
				return false;
			}
		}

		return true;
	}

	hasPermission(permission: string): boolean {
		const user = this.getUser();
		if (!user) return false;

		const rolePermissions: Record<string, string[]> = {
			admin: ["upload", "view", "admin", "delete"],
			uploader: ["upload", "view"],
			viewer: ["view"],
		};

		const userRole = user.role;
		const userGroups = user.groups || [];

		// Check role-based permissions
		if (rolePermissions[userRole]?.includes(permission)) {
			return true;
		}

		// Check group-based permissions
		for (const group of userGroups) {
			if (rolePermissions[group]?.includes(permission)) {
				return true;
			}
		}

		return false;
	}
}

export const authService = AuthService.getInstance();
