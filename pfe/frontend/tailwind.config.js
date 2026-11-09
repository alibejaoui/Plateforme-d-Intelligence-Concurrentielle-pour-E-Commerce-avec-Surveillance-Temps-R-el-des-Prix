/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        dashboard: {
          bg: '#F5F7FA',
          card: '#FFFFFF',
        },
        primary: '#3B82F6',
        'primary-soft': '#93C5FD',
        success: '#22C55E',
        warning: '#F97316',
        'text-primary': '#1F2937',
        'text-secondary': '#6B7280',
        border: '#E5E7EB',
        'bg-soft': '#F5F7FA',
      },
      borderRadius: {
        card: '14px',
      },
      boxShadow: {
        card: '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
        'card-soft': '0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05)',
      },
    },
  },
  plugins: [],
};
