// Copies the Pyodide runtime (Python compiled to WebAssembly) into dist/ so
// the Mock OA can run your code in the browser with no server.
import { cpSync, mkdirSync } from 'node:fs';
const files = ['pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm', 'python_stdlib.zip', 'pyodide-lock.json'];
mkdirSync('dist/pyodide', { recursive: true });
for (const f of files) cpSync(`node_modules/pyodide/${f}`, `dist/pyodide/${f}`);
console.log('copied pyodide runtime to dist/pyodide');
