/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Cores customizadas do projeto
                primary: {
                    DEFAULT: '#6366f1',
                    50: '#eef2ff',
                    100: '#e0e7ff',
                    200: '#c7d2fe',
                    300: '#a5b4fc',
                    400: '#818cf8',
                    500: '#6366f1',
                    600: '#4f46e5',
                    700: '#4338ca',
                    800: '#3730a3',
                    900: '#312e81',
                },
                secondary: {
                    DEFAULT: '#8b5cf6',
                    500: '#8b5cf6',
                    600: '#7c3aed',
                },
                success: {
                    DEFAULT: '#10b981',
                    500: '#10b981',
                },
                error: {
                    DEFAULT: '#ef4444',
                    500: '#ef4444',
                },
                warning: {
                    DEFAULT: '#f59e0b',
                    500: '#f59e0b',
                },
                // Cores de fundo
                background: {
                    DEFAULT: '#0f0f1a',
                    card: '#1a1a2e',
                    hover: '#252540',
                },
                border: {
                    DEFAULT: 'rgba(255, 255, 255, 0.1)',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
