import React from "react";
import {
	BrowserRouter as Router,
	Routes,
	Route,
	Navigate,
} from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider, useAuthContext } from "@/contexts/AuthContext";
import { AuthContainer } from "@/components/auth/AuthContainer";
import { Dashboard } from "@/components/Dashboard";
import { Loader2 } from "lucide-react";

// Protected Route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
	children,
}) => {
	const { isAuthenticated, isLoading } = useAuthContext();

	if (isLoading) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-aws-dark-blue via-aws-squid-ink to-aws-gray-900 flex items-center justify-center">
				<div className="text-center">
					<Loader2 className="h-12 w-12 text-white animate-spin mx-auto mb-4" />
					<p className="text-white text-lg">Loading...</p>
				</div>
			</div>
		);
	}

	return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Public Route component (redirect to dashboard if already authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const { isAuthenticated, isLoading } = useAuthContext();

	if (isLoading) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-aws-dark-blue via-aws-squid-ink to-aws-gray-900 flex items-center justify-center">
				<div className="text-center">
					<Loader2 className="h-12 w-12 text-white animate-spin mx-auto mb-4" />
					<p className="text-white text-lg">Loading...</p>
				</div>
			</div>
		);
	}

	return isAuthenticated ? (
		<Navigate to="/dashboard" replace />
	) : (
		<>{children}</>
	);
};

function App() {
	return (
		<Router>
			<AuthProvider>
				<div className="App">
					<Routes>
						{/* Public routes */}
						<Route
							path="/login"
							element={
								<PublicRoute>
									<AuthContainer />
								</PublicRoute>
							}
						/>
						<Route
							path="/register"
							element={
								<PublicRoute>
									<AuthContainer />
								</PublicRoute>
							}
						/>
						<Route
							path="/confirm"
							element={
								<PublicRoute>
									<AuthContainer />
								</PublicRoute>
							}
						/>

						{/* Protected routes */}
						<Route
							path="/dashboard"
							element={
								<ProtectedRoute>
									<Dashboard />
								</ProtectedRoute>
							}
						/>

						{/* Default redirects */}
						<Route path="/" element={<Navigate to="/dashboard" replace />} />
						<Route path="*" element={<Navigate to="/dashboard" replace />} />
					</Routes>

					<Toaster
						position="top-right"
						toastOptions={{
							duration: 4000,
							style: {
								background: "#363636",
								color: "#fff",
							},
							success: {
								duration: 3000,
								iconTheme: {
									primary: "#16A085",
									secondary: "#fff",
								},
							},
							error: {
								duration: 5000,
								iconTheme: {
									primary: "#E74C3C",
									secondary: "#fff",
								},
							},
						}}
					/>
				</div>
			</AuthProvider>
		</Router>
	);
}

export default App;
