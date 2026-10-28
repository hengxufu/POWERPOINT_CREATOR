#!/usr/bin/env node

import { runExporter } from 'dom-to-pptx/bin/cli-exporter.js';

runExporter(process.argv.slice(2)).catch((err) => {
  console.error('Failed to run exporter:', err);
  process.exit(1);
});
