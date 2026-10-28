#!/usr/bin/env node

import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const c = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  dim: '\x1b[2m',
};

function printHelp() {
  console.log(`
${c.cyan} ____   ___  __  __   _____ ___    ____  ____  _____ ${c.reset}
${c.cyan}|  _ \\ / _ \\|  \\/  | |_   _/ _ \\  |  _ \\|  _ \\|_   _|${c.reset}
${c.cyan}| | | | | | | |\\/| |   | || | | | | |_) | |_) || |  ${c.reset}
${c.cyan}| |_| | |_| | |  | |   | || |_| | |  __/|  __/ | |  ${c.reset}
${c.cyan}|____/ \\___/|_|  |_|   |_| \\___/  |_|   |_|    |_|  ${c.reset}

       ${c.bold}${c.green}C L I   v2.1.2${c.reset}   ${c.dim}— Unified Entry (Skills + Exporter)${c.reset}
       ${c.dim}--------------------------------------------------${c.reset}
`);
  console.log(`${c.bold}Usage:${c.reset}`);
  console.log(
    `  ${c.cyan}dom-to-pptx${c.reset} ${c.yellow}skills${c.reset}                          Launch interactive skills installer`
  );
  console.log(
    `  ${c.cyan}dom-to-pptx${c.reset} ${c.yellow}export${c.reset} ${c.dim}<htmlFile>${c.reset} [options]   Export HTML to .pptx headlessly\n`
  );
  console.log(`For detailed options on exporting, run:`);
  console.log(`  ${c.cyan}dom-to-pptx-exporter --help${c.reset}\n`);
}

async function main() {
  const argv = process.argv.slice(2);
  const command = argv[0];

  if (!command || command === '--help' || command === '-h') {
    printHelp();
    process.exit(0);
  }

  switch (command) {
    case 'skills':
    case 'install-skills': {
      const cliPath = pathToFileURL(path.resolve(__dirname, 'cli-skills-installer.js')).href;
      const { runSkillsInstaller } = await import(cliPath);
      await runSkillsInstaller();
      break;
    }

    case 'export': {
      const exporterPath = pathToFileURL(path.resolve(__dirname, 'cli-exporter.js')).href;
      const { runExporter } = await import(exporterPath);
      await runExporter(argv);
      break;
    }

    default: {
      console.error(`${c.red}❌  Unknown command: "${command}"${c.reset}\n`);
      printHelp();
      process.exit(1);
    }
  }
}

main().catch((err) => {
  console.error(`\n${c.red}Fatal error:${c.reset}`, err.message);
  process.exit(1);
});
