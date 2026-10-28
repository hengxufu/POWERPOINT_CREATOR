#!/usr/bin/env node

import { runSkillsInstaller } from 'dom-to-pptx/bin/cli-skills-installer.js';

runSkillsInstaller().catch((err) => {
  console.error('Failed to run skills installer:', err);
  process.exit(1);
});
