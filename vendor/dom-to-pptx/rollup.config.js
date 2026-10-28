// rollup.config.js
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import polyfillNode from 'rollup-plugin-polyfill-node';
import json from '@rollup/plugin-json';
import fs from 'fs';

// Simple plugin that copies src/animations/animations.css → dist/animations.css after build
const copyCss = {
  name: 'copy-css',
  writeBundle() {
    fs.copyFileSync('src/animations/animations.css', 'dist/animations.css');
    console.log('Copied animations.css → dist/animations.css');

    // Copy transitions if it exists
    if (fs.existsSync('src/animations/transitions.css')) {
      fs.copyFileSync('src/animations/transitions.css', 'dist/transitions.css');
      console.log('Copied transitions.css → dist/transitions.css');
    }
  },
};

const input = 'src/index.js';

// Helper to suppress circular dependency warnings from specific libraries
const onwarn = (warning, warn) => {
  if (warning.code === 'CIRCULAR_DEPENDENCY') {
    // Ignore circular dependencies in these known packages
    if (
      warning.message.includes('node_modules/readable-stream') ||
      warning.message.includes('node_modules/jszip') ||
      warning.message.includes('node_modules/semver')
    ) {
      return;
    }
  }
  warn(warning);
};

// --- CONFIG A: Library (NPM) ---
// Does NOT include dependencies. Consumers (Webpack/Vite) will bundle them.
const configLibrary = {
  input,
  output: [
    {
      file: 'dist/dom-to-pptx.mjs',
      format: 'es',
      sourcemap: true,
    },
    {
      file: 'dist/dom-to-pptx.cjs',
      format: 'cjs',
      sourcemap: true,
      exports: 'named',
    },
  ],
  plugins: [
    resolve({ preferBuiltins: true }), // Allow node resolution
    commonjs(),
    json(),
  ],
  // Mark all dependencies as external so they aren't bundled into the .mjs/.cjs files
  external: ['pptxgenjs', 'html2canvas', 'jszip', 'fonteditor-core', 'opentype.js', 'pako'],
  onwarn,
};

// --- CONFIG B: Browser Bundle (CDN) ---
// Includes EVERYTHING (Polyfills + Dependencies). Standalone file.
const configBundle = {
  input,
  output: {
    file: 'dist/dom-to-pptx.bundle.js',
    format: 'umd',
    name: 'domToPptx',
    esModule: false,
    sourcemap: false,
    inlineDynamicImports: true,
    // Inject global variables for browser compatibility
    intro: `
      var global = typeof self !== "undefined" ? self : this; 
      var process = { env: { NODE_ENV: "production" } };
    `,
    globals: {
      // If you want users to load PptxGenJS separately via script tag, keep this.
      // If you want to bundle PptxGenJS inside, remove it from external/globals.
      // Usually for "bundle.js", we bundle everything except maybe very large libs.
      // Based on your previous config, we are bundling everything.
    },
  },
  plugins: [
    // 1. JSON plugin (needed for some deps)
    json(),

    // 2. Resolve browser versions of modules
    resolve({
      browser: true,
      preferBuiltins: false, // Force use of browser polyfills
    }),

    // 3. Convert CJS to ESM
    commonjs({
      transformMixedEsModules: true,
    }),

    // 4. Inject Node.js Polyfills (Buffer, Stream, etc.)
    polyfillNode(),

    // 5. Copy animations.css to dist/
    copyCss,
  ],
  // Empty external list means "Bundle everything"
  external: [],
  onwarn,
};

// --- CONFIG C: Node Exporter ---
// The node exporter always runs inside Node.js where node_modules is available,
// so we externalize ALL bare package imports (node built-ins + every npm dep).
// This prevents rollup from trying to bundle transitive deps like
// @puppeteer/browsers → escodegen → JSON (which would break without the json plugin).
const configNode = {
  input: 'src/node-exporter.js',
  output: [
    {
      file: 'dist/dom-to-pptx-node.mjs',
      format: 'es',
      sourcemap: true,
    },
    {
      file: 'dist/dom-to-pptx-node.cjs',
      format: 'cjs',
      sourcemap: true,
      exports: 'named',
    },
  ],
  plugins: [resolve({ preferBuiltins: true }), commonjs(), json()],
  // Externalize bare npm specifiers (e.g. 'fs', 'puppeteer', '@puppeteer/browsers').
  // Crucially we must NOT externalize the entry module 'src/node-exporter.js',
  // which Rollup passes through this function before resolving.
  // Rule: a bare specifier never starts with '.' or '/' and if it's not scoped (@)
  // it contains no path separators at all.
  external: (id) => {
    if (id.startsWith('.') || id.startsWith('/') || id.startsWith('\\')) return false; // relative / absolute
    if (/^[A-Za-z]:\\/.test(id)) return false; // Windows absolute path (C:\...)
    if (id.startsWith('@')) return true; // scoped package: @scope/pkg
    return !id.includes('/') && !id.includes('\\'); // plain package: fs, puppeteer, etc.
  },
  onwarn,
};

export default [configLibrary, configBundle, configNode];
