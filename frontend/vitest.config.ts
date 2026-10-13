import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
  // tsconfig.json sets "jsx": "preserve" for Next.js's own SWC compiler to
  // handle - tsc itself is type-check-only. Vite's transform reads that same
  // setting and, given "preserve", stops transforming JSX itself, so tests
  // need their own tsconfig with a JSX mode Vite can actually compile.
  tsconfig: './tsconfig.vitest.json',
  resolve: { alias: { '@': path.resolve(__dirname, '.') } },
  test: { environment: 'node', include: ['tests/**/*.test.ts'] },
});
