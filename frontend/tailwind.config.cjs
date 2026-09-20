/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{ts,tsx,js,jsx}',
    './components/**/*.{ts,tsx,js,jsx}',
    './pages/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        templeGold: '#efb538ff',
        templeWhite: '#F5F1E8',
        templeDark: '#0B1220',
        maroon: { DEFAULT: '#7a1c1c', dark: '#5a1010', light: '#a83232' },
        saffron: { DEFAULT: '#d97a1f', light: '#f2b45a' },
        cream: '#fbf6ec',
      },
      fontFamily: {
        serif: ['Georgia', 'Cambria', '"Times New Roman"', 'serif'],
      },
      keyframes: {
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
      animation: {
        slideIn: 'slideIn 0.6s ease-out',
      },
    },
  },
  plugins: [],
}
