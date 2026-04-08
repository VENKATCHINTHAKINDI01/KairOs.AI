/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"DM Serif Display"', 'serif'],
        body:    ['"DM Sans"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        night:   { DEFAULT: '#0a0a0f', 50: '#1a1a2e', 100: '#16213e' },
        kairos:  { DEFAULT: '#e8552a', light: '#ff7a4a', dark: '#c43d18' },
        signal:  { green: '#00d97e', amber: '#f5a623', red: '#e8552a' },
        slate:   { 850: '#1e2130', 900: '#161928', 950: '#0d0f1a' },
      },
      animation: {
        'pulse-slow':   'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'slide-up':     'slideUp 0.4s ease-out',
        'fade-in':      'fadeIn 0.3s ease-out',
        'trace-scroll': 'traceScroll 0.2s ease-out',
      },
      keyframes: {
        slideUp:  { from: { transform: 'translateY(12px)', opacity: 0 }, to: { transform: 'translateY(0)', opacity: 1 } },
        fadeIn:   { from: { opacity: 0 }, to: { opacity: 1 } },
      },
    },
  },
  plugins: [],
}