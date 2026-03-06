/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: '#0b1120',
                secondary: '#111827',
                card: '#1f2937',
                accent: '#3b82f6',
                textPrimary: '#e5e7eb',
                textSecondary: '#9ca3af',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
