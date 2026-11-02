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
        petalFall: 'petalFall 6s linear infinite',
        glowPulse: 'glowPulse 3.5s ease-in-out infinite',
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
