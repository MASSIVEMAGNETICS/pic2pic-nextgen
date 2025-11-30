/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				surface: {
					DEFAULT: '#1e1e2e',
					light: '#313244'
				},
				primary: {
					DEFAULT: '#6366f1',
					dark: '#4f46e5'
				},
				secondary: '#22d3ee',
				accent: '#f472b6'
			}
		}
	},
	plugins: []
};
