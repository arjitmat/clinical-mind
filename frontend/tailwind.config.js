/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'cream-white': '#FFFCF7',
        'warm-gray': {
          50: '#F5F3F0',
          100: '#E8E5E0',
          200: '#D4D0CA',
          900: '#2A2520',
        },
        'forest-green': {
          DEFAULT: '#2D5C3F',
          dark: '#234730',
        },
        'sage-green': '#6B8E6F',
        'terracotta': '#C85835',
        'soft-blue': '#4A7C8C',
        'success': '#2D5C3F',
        'warning': '#D4803F',
        'error': '#C85835',
        'text': {
          primary: '#2A2520',
          secondary: '#5A5147',
          tertiary: '#8A8179',
        },
      },
      fontSize: {
        xs: '0.875rem',
        sm: '1rem',
        base: '1.125rem',
        lg: '1.375rem',
        xl: '1.75rem',
        '2xl': '2.25rem',
        '3xl': '3rem',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        lg: '12px',
        xl: '16px',
        '2xl': '24px',
      },
    },
  },
  plugins: [],
}
