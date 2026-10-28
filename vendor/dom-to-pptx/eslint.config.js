import globals from 'globals';
import pluginJs from '@eslint/js';
import markdown from '@eslint/markdown';
import pluginPrettier from 'eslint-config-prettier';

export default [
  { ignores: ['dist/**', 'scratch/**'] },
  {
    files: ['**/*.js'],
    languageOptions: { sourceType: 'module', globals: { ...globals.browser } },
  },
  {
    files: ['**/*.md'],
    plugins: {
      markdown,
    },
    language: 'markdown/commonmark',
  },
  {
    files: [
      'bin/**/*.js',
      'scripts/**/*.js',
      'packages/**/*.js',
      'src/node-exporter.js',
      'rollup.config.js',
      'vitest.config.js',
      'eslint.config.js',
    ],
    languageOptions: { globals: { ...globals.node } },
  },
  {
    files: ['**/*.js'],
    ...pluginJs.configs.recommended,
  },
  pluginPrettier,
  {
    files: ['**/*.js'],
    rules: {
      'no-unused-vars': 'warn',
      'no-undef': 'warn',
      'preserve-caught-error': 'off',
    },
  },
];
