/** @type {import('tailwindcss').Config} */
// Every color scale points at CSS variables so the two themes
// (paper notebook / night desk) swap in index.css without touching components.
const SHADES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950];
const scale = (name) =>
  Object.fromEntries(SHADES.map((s) => [s, `rgb(var(--${name}-${s}) / <alpha-value>)`]));

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        zinc: scale('ink'),
        violet: scale('py'),
        amber: scale('hl'),
        emerald: scale('ok'),
        rose: scale('pen'),
        sky: scale('sky'),
        orange: scale('or'),
      },
      fontFamily: {
        sans: ['"Bricolage Grotesque"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
};
