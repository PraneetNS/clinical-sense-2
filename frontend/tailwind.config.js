/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                navy: {
                    900: '#0a0f1e',
                    800: '#0f172a',
                    700: '#1a2340',
                    600: '#1e293b',
                },
                electric: {
                    400: '#60a5fa',
                    500: '#3b82f6',
                    600: '#2563eb',
                },
                emerald: {
                    400: '#34d399',
                    500: '#10b981',
                    600: '#059669',
                },
            },
            backgroundImage: {
                "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
                "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
                "gradient-dark": "linear-gradient(to bottom, #0f172a, #020617)",
            },
            animation: {
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'float': 'float 6s ease-in-out infinite',
                'float-delayed': 'float 6s ease-in-out 2s infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
                'shimmer': 'shimmer 2s linear infinite',
                'heartbeat': 'heartbeat 2s ease-in-out infinite',
                'typing': 'typing 3.5s steps(40, end) infinite',
                'blink': 'blink 1s step-end infinite',
                'flow-line': 'flowLine 3s linear infinite',
                'neural-pulse': 'neuralPulse 3s ease-in-out infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%': { transform: 'translateY(-20px)' },
                },
                glow: {
                    '0%': { boxShadow: '0 0 5px rgba(59, 130, 246, 0.3), 0 0 10px rgba(59, 130, 246, 0.1)' },
                    '100%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(59, 130, 246, 0.2)' },
                },
                shimmer: {
                    '0%': { backgroundPosition: '-200% 0' },
                    '100%': { backgroundPosition: '200% 0' },
                },
                heartbeat: {
                    '0%, 100%': { transform: 'scale(1)', opacity: '0.3' },
                    '14%': { transform: 'scale(1.05)', opacity: '0.5' },
                    '28%': { transform: 'scale(1)', opacity: '0.3' },
                    '42%': { transform: 'scale(1.08)', opacity: '0.6' },
                    '70%': { transform: 'scale(1)', opacity: '0.3' },
                },
                typing: {
                    '0%': { width: '0' },
                    '50%': { width: '100%' },
                    '100%': { width: '0' },
                },
                blink: {
                    '50%': { borderColor: 'transparent' },
                },
                flowLine: {
                    '0%': { strokeDashoffset: '100' },
                    '100%': { strokeDashoffset: '0' },
                },
                neuralPulse: {
                    '0%, 100%': { opacity: '0.3', transform: 'scale(0.95)' },
                    '50%': { opacity: '1', transform: 'scale(1)' },
                },
            },
        },
    },
    plugins: [],
};
