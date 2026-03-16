/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4F46E5',
        primaryHover: '#4338CA',
        secondaryGray: '#6B7280',
        successGreen: '#10B981',
        warningAmber: '#F59E0B',
        errorRed: '#EF4444',
        infoBlue: '#3B82F6',
        bgPage: '#F9FAFB',
        surface: '#FFFFFF',
        borderColor: '#E5E7EB',
        textPrimary: '#111827',
        textSecondary: '#6B7280',
        textMuted: '#9CA3AF',
        lowRisk: '#D1FAE5',
        mediumRisk: '#FEF3C7',
        highRisk: '#FEE2E2',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}































