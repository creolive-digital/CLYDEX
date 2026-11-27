import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import {copyFileSync, mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

const root = import.meta.dirname;

export default defineConfig({
  plugins: [react(), {name: 'local-license-notices', closeBundle() {
    const folder = resolve(root, '../deployment/windows/artifacts/frontend/licenses'); mkdirSync(folder, {recursive: true});
    for (const [source, name] of [['../assets/fonts/Orbitron-OFL.txt','Orbitron-OFL.txt'],['legacy/spacegrotesk-license.txt','SpaceGrotesk-OFL.txt'],['node_modules/react/LICENSE','React-MIT.txt'],['node_modules/react-dom/LICENSE','ReactDOM-MIT.txt'],['node_modules/three/LICENSE','Three-MIT.txt'],['node_modules/lucide-react/LICENSE','Lucide-ISC.txt']]) copyFileSync(resolve(root,source),resolve(folder,name));
  }}], base: './',
  server: {host: '127.0.0.1', fs: {allow: ['..']}},
  build: {outDir: '../deployment/windows/artifacts/frontend', emptyOutDir: true, target: 'es2022', sourcemap: false},
  test: {environment: 'jsdom', setupFiles: ['./tests/setup.ts'], include: ['tests/**/*.test.{ts,tsx}']},
});
