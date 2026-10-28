#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Ensure the cursor is always brought back if the user exits unexpectedly
process.on('exit', () => process.stdout.write('\x1b[?25h'));

const printLogo = () => {
  const logo = `
\x1b[36m ____   ___  __  __   _____ ___    ____  ____ _____ \x1b[0m
\x1b[36m|  _ \\ / _ \\|  \\/  | |_   _/ _ \\  |  _ \\|  _ \\_   _|\x1b[0m
\x1b[1;36m| | | | | | | |\\/| |   | || | | | | |_) | |_) || |  \x1b[0m
\x1b[1;36m| |_| | |_| | |  | |   | || |_| | |  __/|  __/ | |  \x1b[0m
\x1b[36m|____/ \\___/|_|  |_|   |_| \\___/  |_|   |_|    |_|  \x1b[0m

       \x1b[1;32mS K I L L S   I N S T A L L E R  (v2.1)\x1b[0m
       \x1b[90m--------------------------------------\x1b[0m
`;
  console.log(logo);
};

const printHelp = () => {
  printLogo();
  console.log('\x1b[1mUsage:\x1b[0m');
  console.log('  \x1b[36mdom-to-pptx-skills\x1b[0m [options]\n');
  console.log('\x1b[1mOptions:\x1b[0m');
  console.log('  \x1b[33m--help, -h\x1b[0m                Show this help message\n');
  console.log('\x1b[1mDescription:\x1b[0m');
  console.log('  An interactive utility to install presentation engineering skills to your AI agents.');
  console.log('  It scans standard user directories for Claude Code, Gemini CLI, Cursor, and Windsurf.');
  console.log('  You can also install the skill locally to the current folder (`.agent/skills`).\n');
};

/**
 * Interactive Multi-select Checkbox UI
 */
async function multiselect(questionText, options) {
  return new Promise((resolve) => {
    let cursor = 0;

    const render = (firstRender = false) => {
      // If not the first render, move cursor up by the number of options and clear
      if (!firstRender) {
        process.stdout.write(`\x1b[${options.length + 1}A\x1b[G\x1b[J`);
      }

      let output = `\x1b[36m? \x1b[0m\x1b[1m${questionText}\x1b[0m \x1b[90m(<space> to select, <enter> to confirm)\x1b[0m\n`;

      options.forEach((opt, i) => {
        const isHover = i === cursor;
        const isSelected = opt.selected;
        const prefix = isHover ? '\x1b[36m❯\x1b[0m' : ' ';
        const checkbox = isSelected ? '\x1b[32m●\x1b[0m' : '\x1b[90m○\x1b[0m';
        const labelColor = isSelected ? '\x1b[32m' : isHover ? '\x1b[36m' : '\x1b[0m';

        output += `  ${prefix} ${checkbox} ${labelColor}${opt.name}\x1b[0m`;
        output += '\n';
      });

      process.stdout.write(output);
    };

    const cleanup = () => {
      process.stdin.setRawMode(false);
      process.stdin.pause();
      process.stdout.write('\x1b[?25h\n'); // Show cursor and move to new line
    };

    const handleInput = (data) => {
      const key = data.toString();

      if (key === '\u0003') {
        // Ctrl+C
        cleanup();
        process.exit(0);
      } else if (key === '\r' || key === '\n') {
        // Enter
        cleanup();
        resolve(options.filter((o) => o.selected));
      } else if (key === ' ') {
        // Space
        options[cursor].selected = !options[cursor].selected;
        render();
      } else if (key === '\u001b[A' || key === 'k') {
        // Up arrow / vim 'k'
        cursor = cursor > 0 ? cursor - 1 : options.length - 1;
        render();
      } else if (key === '\u001b[B' || key === 'j') {
        // Down arrow / vim 'j'
        cursor = cursor < options.length - 1 ? cursor + 1 : 0;
        render();
      }
    };

    process.stdout.write('\x1b[?25l'); // Hide cursor
    render(true);

    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.setEncoding('utf8');
    process.stdin.removeAllListeners('data');
    process.stdin.on('data', handleInput);
  });
}

/**
 * Interactive Y/N Confirmation
 */
async function confirm(questionText) {
  return new Promise((resolve) => {
    process.stdout.write(`\x1b[36m? \x1b[0m\x1b[1m${questionText}\x1b[0m \x1b[90m(Y/n)\x1b[0m `);

    const cleanup = () => {
      process.stdin.setRawMode(false);
      process.stdin.pause();
      console.log();
    };

    const handleInput = (data) => {
      const key = data.toString().toLowerCase();

      if (key === '\u0003') {
        // Ctrl+C
        cleanup();
        process.exit(0);
      } else if (key === 'n') {
        process.stdout.write('n');
        cleanup();
        resolve(false);
      } else if (key === 'y' || key === '\r' || key === '\n') {
        // Default to Yes on Enter
        process.stdout.write('Y');
        cleanup();
        resolve(true);
      }
    };

    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.setEncoding('utf8');
    process.stdin.removeAllListeners('data');
    process.stdin.on('data', handleInput);
  });
}

function copyRecursiveSync(src, dest) {
  const exists = fs.existsSync(src);
  const stats = exists && fs.statSync(src);
  const isDirectory = exists && stats.isDirectory();

  if (isDirectory) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    fs.readdirSync(src).forEach((childItemName) => {
      copyRecursiveSync(path.join(src, childItemName), path.join(dest, childItemName));
    });
  } else {
    fs.copyFileSync(src, dest);
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) {
    printHelp();
    return;
  }

  if (!process.stdin.isTTY || typeof process.stdin.setRawMode !== 'function') {
    throw new Error('Interactive terminal session is not supported in this environment.');
  }

  printLogo();

  const homeDir = process.env.HOME || process.env.USERPROFILE || process.env.HOMEPATH;

  // Define known agents and their detection folders
  const agents = [
    { name: 'Claude Code', path: path.join(homeDir, '.claude', 'skills') },
    { name: 'Gemini CLI / Antigravity (Global)', path: path.join(homeDir, '.gemini', 'antigravity', 'global_skills') },
    { name: 'Gemini CLI / Antigravity (Local)', path: path.join(homeDir, '.gemini', 'antigravity', 'skills') },
    { name: 'Gemini CLI / Antigravity (User)', path: path.join(homeDir, '.gemini', 'skills') },
    { name: 'Gemini CLI / Antigravity (IDE)', path: path.join(homeDir, '.gemini', 'antigravity-ide', 'skills') },
    { name: 'Windsurf', path: path.join(homeDir, '.windsurf', 'skills') },
    { name: 'Cursor', path: path.join(homeDir, '.cursor', 'skills') },
  ];

  // Auto-detect installed agents
  const detectedAgents = agents.filter((a) => fs.existsSync(path.dirname(a.path)));
  const projectLocalPath = path.join(process.cwd(), '.agent', 'skills');

  // Prepare UI Options
  const installOptions = detectedAgents.map((a) => ({
    name: a.name,
    path: a.path,
    selected: true, // Default checked if detected
  }));

  // Always offer project-local installation
  installOptions.push({
    name: 'Project Local (.agent/skills)',
    path: projectLocalPath,
    selected: detectedAgents.length === 0, // Default checked if NO other agents detected
  });

  if (detectedAgents.length === 0) {
    console.log(
      '\n\x1b[33m⚠️  No global AI agent directories detected on your system (e.g. Claude Code, Gemini CLI, Cursor, Windsurf).\x1b[0m'
    );
    console.log('\x1b[36m💡  Try:\x1b[0m');
    console.log('  1. Select "Project Local" to install the skill to this project\'s workspace.');
    console.log('  2. Check if your AI agent is installed and configured in your user home folder.');
    console.log('  3. Refer to your agent documentation to find where custom skills/plugins are loaded.\n');
  }

  try {
    const selectedOptions = await multiselect('Select target locations to install the skill:', installOptions);

    if (selectedOptions.length === 0) {
      console.log('\n\x1b[33mNo locations selected. Installation cancelled.\x1b[0m\n');
      return;
    }

    const targetsToInstall = selectedOptions.map((o) => o.path);

    // Confirm installation targets
    console.log('\n\x1b[1mInstalling to the following target(s):\x1b[0m');
    targetsToInstall.forEach((t) =>
      console.log(`  \x1b[36m❯\x1b[0m \x1b[32m${path.join(t, 'dom-to-pptx-skill')}\x1b[0m`)
    );
    console.log();

    const proceed = await confirm('Proceed with installation?');
    if (!proceed) {
      console.log('\x1b[33mAborted.\x1b[0m\n');
      return;
    }

    // Execution
    let subpackageSkillsDir = null;
    try {
      // If dom-to-pptx-skills is installed in node_modules or linked
      const skillsPkgJson = import.meta.resolve ? import.meta.resolve('dom-to-pptx-skills/package.json') : null;
      if (skillsPkgJson) {
        subpackageSkillsDir = path.join(fileURLToPath(skillsPkgJson), '..', 'skills', 'dom-to-pptx-skill');
      }
    } catch {
      // Ignored if not found
    }

    const candidates = [
      subpackageSkillsDir,
      path.join(__dirname, '..', 'packages', 'dom-to-pptx-skills', 'skills', 'dom-to-pptx-skill'),
      path.join(__dirname, '..', 'skills', 'dom-to-pptx-skill'),
      path.join(__dirname, 'skills', 'dom-to-pptx-skill'),
    ].filter(Boolean);

    const sourceDir = candidates.find((dir) => fs.existsSync(dir));

    if (!sourceDir) {
      throw new Error(`Source skills not found in candidate paths (${candidates.join(', ')}). Are you running from the package root or is dom-to-pptx-skills installed?`);
    }

    for (const base of targetsToInstall) {
      const targetDir = path.join(base, 'dom-to-pptx-skill');
      copyRecursiveSync(sourceDir, targetDir);
    }

    console.log('\n\x1b[32m%s\x1b[0m', '✅ Success! dom-to-pptx "Atmospheric UI" skills installed.');
    console.log('\x1b[90mYour agent(s) are now equipped with the Premium Presentation Engineering framework.\x1b[0m');
    console.log('\x1b[33mNote: You may need to restart your AI agent to see the new skill.\x1b[0m\n');
  } catch (err) {
    // Failsafe cursor restore
    if (process.stdin.isTTY && typeof process.stdin.setRawMode === 'function') {
      process.stdout.write('\x1b[?25h');
    }
    console.error('\n\x1b[31m%s\x1b[0m', '❌ Error during installation:');
    console.error(err.message);
    console.log('\n\x1b[36m💡  Try:\x1b[0m');
    if (err.message.includes('Interactive terminal session')) {
      console.log('  - Run this command in an interactive command line shell (like CMD, PowerShell, or Bash).');
      console.log('  - Avoid piping stdin/stdout or executing via automated runner scripts.');
    } else if (err.message.includes('Source skills not found')) {
      console.log('  - Ensure you are running the installation script from the root of the "dom-to-pptx" package.');
      console.log('  - Verify that the "skills/dom-to-pptx-skill" directory exists in the package folder.');
    } else if (err.code === 'EACCES' || err.code === 'EPERM') {
      console.log(
        '  - This looks like a permission issue. Try running the command with administrator/sudo privileges.'
      );
      console.log('  - Check write access to your target directories.');
    } else {
      console.log('  - Verify that the target directories exist and are writable.');
      console.log('  - Check the error stack above for specific file access failures.');
    }
    console.log();
  }
}

export { main as runSkillsInstaller };

// Auto-run only when this file is executed directly (not imported)
const isMain =
  process.argv[1] &&
  (process.argv[1].endsWith('cli-skills-installer.js') ||
    process.argv[1].endsWith('cli.js') ||
    process.argv[1].endsWith('dom-to-pptx-skills'));
if (isMain) {
  main()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error(err);
      process.exit(1);
    });
}
