/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
	theme: {
		extend: {
			colors: {
				// AWS Color Palette
				"aws-orange": "#FF9900",
				"aws-dark-blue": "#232F3E",
				"aws-light-blue": "#4A90E2",
				"aws-squid-ink": "#161E2D",
				"aws-gray": {
					100: "#F2F3F3",
					200: "#EAEDED",
					300: "#D5DBDB",
					400: "#AAB7B8",
					500: "#85929E",
					600: "#5D6D7E",
					700: "#34495E",
					800: "#2C3E50",
					900: "#1B2631",
				},
				// Status Colors
				success: "#16A085",
				warning: "#F39C12",
				error: "#E74C3C",
				info: "#4A90E2",
			},
			fontFamily: {
				inter: ["Inter", "system-ui", "sans-serif"],
			},
			animation: {
				"fade-in": "fadeIn 0.5s ease-in-out",
				"slide-up": "slideUp 0.3s ease-out",
				"pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
			},
			keyframes: {
				fadeIn: {
					"0%": { opacity: "0" },
					"100%": { opacity: "1" },
				},
				slideUp: {
					"0%": { transform: "translateY(10px)", opacity: "0" },
					"100%": { transform: "translateY(0)", opacity: "1" },
				},
			},
		},
	},
	plugins: [],
};
