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
        templeGoldDark: '#8a5a00', // gold for text on light backgrounds (5:1+)
        templeWhite: '#F5F1E8',
        templeDark: '#0B1220',
        maroon: { DEFAULT: '#7a1c1c', dark: '#5a1010', light: '#a83232' },
        // dark: the shade for text and for buttons with white text - DEFAULT is under 4.5:1 on light backgrounds
        saffron: { DEFAULT: '#d97a1f', light: '#f2b45a', dark: '#a3530e' },
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
        // /tv: single petals drifting down the whole screen
        petalFall: {
          '0%': { transform: 'translateY(-10%) rotate(0deg)', opacity: '0' },
          '10%': { opacity: '0.9' },
          '90%': { opacity: '0.9' },
          '100%': { transform: 'translateY(115vh) rotate(200deg)', opacity: '0' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        marquee: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        gradientShift: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '100% 50%' },
        },
        spinSlow: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
        kenburns: {
          '0%': { transform: 'scale(1) translate(0, 0)' },
          '100%': { transform: 'scale(1.12) translate(-2%, -1.5%)' },
        },
        flicker: {
          '0%, 100%': { transform: 'scale(1, 1)', opacity: '1' },
          '30%': { transform: 'scale(0.92, 1.08)', opacity: '0.85' },
          '60%': { transform: 'scale(1.05, 0.95)', opacity: '1' },
        },
        progress: {
          '0%': { width: '0%' },
          '100%': { width: '100%' },
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
        petalFall: 'petalFall 10s linear infinite',
        fadeUp: 'fadeUp 0.9s ease-out both',
        gradientShift: 'gradientShift 40s ease-in-out infinite alternate',
        spinSlow: 'spinSlow 150s linear infinite',
        shimmer: 'shimmer 8s linear infinite',
        kenburns: 'kenburns 14s ease-out both',
        flicker: 'flicker 1.6s ease-in-out infinite',
        progress: 'progress 12s linear both', // keep in step with SCENE_MS in app/tv/page.tsx
        marquee: 'marquee 40s linear infinite',
      },
    },
  },
  plugins: [],
}
