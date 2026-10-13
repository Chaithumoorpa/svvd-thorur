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
        // Each petal's layer covers the whole blessing card, so these % offsets are
        // fractions of the card: petals leave the Om and drift down over the photo.
        petalShower: {
          '0%': { transform: 'translate(0, 0) rotate(0deg) scale(0.3)', opacity: '0' },
          '12%': { transform: 'translate(calc(var(--dx) * 0.15), 3%) rotate(30deg) scale(1)', opacity: '1' },
          '85%': { opacity: '0.95' },
          '100%': { transform: 'translate(var(--dx), var(--dy)) rotate(var(--rot)) scale(1)', opacity: '0' },
        },
        glowPulse: {
          '0%, 100%': { opacity: '0.55', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.08)' },
        },
      },
      animation: {
        slideIn: 'slideIn 0.6s ease-out',
        petalShower: 'petalShower 5s ease-in infinite',
        glowPulse: 'glowPulse 3.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
