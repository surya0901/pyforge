import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';

// Optional: `npx vite build -c vite.single.config.ts` produces one self-contained
// HTML file (dist-single/index.html) you can open directly or host anywhere.
export default defineConfig({
  base: './',
  plugins: [react(), viteSingleFile()],
  build: { outDir: 'dist-single' },
});
