import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base: './' makes every asset path relative, so the build works on
// GitHub Pages project sites (username.github.io/repo-name/) with no edits.
export default defineConfig({
  base: './',
  plugins: [react()],
});
