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
        petalFall: {
          '0%': { transform: 'translateY(-10%) rotate(0deg)', opacity: '0' },
          '10%': { opacity: '0.9' },
          '90%': { opacity: '0.9' },
          '100%': { transform: 'translateY(340%) rotate(200deg)', opacity: '0' },
        },
        glowPulse: {
          '0%, 100%': { opacity: '0.55', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.08)' },
        },
      },
      animation: {
        slideIn: 'slideIn 0.6s ease-out',
        petalFall: 'petalFall 6s linear infinite',
        glowPulse: 'glowPulse 3.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
