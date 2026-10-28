#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

const builder = require('./build_deck_pptxgenjs');
const { getPreset } = require('../templates/pptxgenjs/presets');
const slideRenderers = require('../templates/pptxgenjs/slides');
const { contractsForGrammar } = require('../templates/pptxgenjs/role_layout_contracts');

const ROOT = path.resolve(__dirname, '..');
const GRAMMARS = [
  ['consulting-answer-pyramid', 'arctic-minimal', 'Answer Pyramid'],
  ['scientific-evidence-plate', 'lab-report', 'Evidence Plate'],
  ['clinical-care-pathway', 'executive-clinical', 'Care Pathway'],
  ['editorial-spread', 'editorial-minimal', 'Editorial Spread'],
  ['investor-thesis-stage', 'sunset-investor', 'Thesis Stage'],
  ['operations-grid', 'lavender-ops', 'Operating Grid'],
  ['policy-public-docket', 'warm-terracotta', 'Public Docket'],
  ['technical-telemetry-canvas', 'midnight-neon', 'Telemetry Canvas'],
];

function parseArgs(argv) {
  const args = {
    output: path.join(ROOT, 'examples', 'v0.9_full_deck_taste_grammar_gallery.pptx'),
    manifest: '',
    adapterProof: false,
  };
  for (let index = 2; index < argv.length; index += 1) {
    if (argv[index] === '--output' && argv[index + 1]) {
      args.output = argv[index + 1];
      index += 1;
    } else if (argv[index] === '--manifest' && argv[index + 1]) {
      args.manifest = argv[index + 1];
      index += 1;
    } else if (argv[index] === '--adapter-proof') {
      args.adapterProof = true;
    }
  }
  return args;
}

function roleSlides(grammarLabel, adapterProof = false) {
  const footer = `Urban heat resilience pilot | ${grammarLabel}`;
  if (adapterProof) {
    return [
      {
        type: 'title', role: 'title', proof_role: 'title_alternate', role_layout_variant: 'alternate',
        title: 'Cooling the Last 5 Degrees',
        subtitle: 'A neighborhood heat-resilience pilot designed for measurable relief, accountable delivery, and a 90-day decision.',
        kicker: grammarLabel, footer,
      },
      {
        type: 'section', role: 'section', proof_role: 'section_dense', role_layout_variant: 'dense',
        title: 'From exposure to action',
        subtitle: 'Locate the hottest blocks, test three interventions, then scale only what improves lived conditions.',
        section_number: '02', footer,
      },
      {
        type: 'content', role: 'evidence', proof_role: 'evidence_cards_2', variant: 'cards-2',
        role_layout_variant: 'primary', title: 'Two conditions make a targeted pilot testable',
        subtitle: 'Concentrated exposure and a measurable intervention window',
        cards: [
          { title: 'Concentrated heat', body: 'Fourteen blocks carry the highest combined exposure and vulnerability score.' },
          { title: 'Observable response', body: 'Surface temperature and resident comfort can both be measured inside ninety days.' },
        ],
        footer,
      },
      {
        type: 'content', role: 'evidence', proof_role: 'evidence_cards_3', variant: 'cards-3',
        role_layout_variant: 'alternate', title: 'The pilot joins place, intervention, and proof',
        subtitle: 'Three editable evidence cards routed through mirrored grammar slots',
        cards: [
          { title: 'Place', body: 'Prioritize the hottest blocks with low canopy and high resident vulnerability.' },
          { title: 'Intervention', body: 'Pair durable shade with rapidly deployable cooling measures.' },
          { title: 'Proof', body: 'Require temperature relief, comfort improvement, and manageable upkeep.' },
        ],
        footer,
      },
      {
        type: 'content', role: 'evidence', proof_role: 'evidence_timeline', variant: 'timeline',
        role_layout_variant: 'dense', title: 'A ninety-day cycle converts evidence into a scale decision',
        subtitle: 'Milestones remain editable while the grammar controls their spatial hierarchy',
        milestones: [
          { label: 'D14', title: 'Baseline', body: 'Sensors and resident pulse active across fourteen blocks.' },
          { label: 'D30', title: 'Deploy', body: 'Shade, cool-roof, and rapid-cooling cohorts begin.' },
          { label: 'D60', title: 'Compare', body: 'Temperature, comfort, uptime, and upkeep are reviewed.' },
          { label: 'D90', title: 'Decide', body: 'Scale, revise, or stop each intervention.' },
        ],
        footer,
      },
      ...roleSlides(grammarLabel, false).slice(3).map((slide, index) => ({
        ...slide,
        proof_role: ['comparison', 'chart', 'table', 'decision', 'references'][index],
        role_layout_variant: index % 3 === 0 ? 'alternate' : (index % 3 === 1 ? 'dense' : 'primary'),
      })),
    ];
  }
  return [
    {
      type: 'title', role: 'title', title: 'Cooling the Last 5 Degrees',
      subtitle: 'A neighborhood heat-resilience pilot designed for measurable relief, accountable delivery, and a 90-day decision.',
      footer,
    },
    {
      type: 'section', role: 'section', title: 'From exposure to action',
      subtitle: 'Locate the hottest blocks, test three interventions, then scale only what improves lived conditions.',
      footer,
    },
    {
      type: 'content', role: 'evidence', treatment_key: 'dashboard', variant: 'stats',
      title: 'Heat exposure is concentrated enough to make a targeted pilot testable',
      subtitle: 'Three evidence anchors before intervention',
      facts: [
        { value: '5.2°C', label: 'Peak heat gap', detail: 'versus city median' },
        { value: '14', label: 'Priority blocks', detail: 'high exposure + vulnerability' },
        { value: '38%', label: 'Low canopy', detail: 'below target coverage' },
      ],
      summary_callout: 'A small geography carries a disproportionate share of the risk.',
      footer,
    },
    {
      type: 'content', role: 'comparison', treatment_key: 'comparison', variant: 'comparison-2col',
      title: 'Permanent shade creates durable value; rapid cooling buys learning speed',
      subtitle: 'Two complementary intervention postures',
      left: {
        title: 'Build durable shade',
        bullets: ['Tree and canopy corridors', 'Higher setup cost', 'Long-lived neighborhood benefit'],
      },
      right: {
        title: 'Deploy rapid cooling',
        bullets: ['Cool roofs and misting stops', 'Fast deployment', 'Shorter asset life'],
      },
      verdict: 'Pair one durable corridor with two rapid-cooling test blocks.',
      footer,
    },
    {
      type: 'content', role: 'chart', treatment_key: 'chart', variant: 'chart',
      title: 'The combined intervention is expected to close most of the heat gap',
      subtitle: 'Modeled peak surface-temperature reduction',
      chart: {
        type: 'bar', title: 'Peak surface-temperature reduction',
        labels: ['Shade', 'Cool roof', 'Combined', 'Target'], values: [1.8, 2.4, 4.1, 4.5],
        facts: [
          { value: '4.1°C', label: 'Combined', detail: 'modeled reduction' },
          { value: '91%', label: 'Of target', detail: 'before field correction' },
        ],
        notes: 'Synthetic planning model for release demonstration; editable native chart.',
      },
      caption: 'Illustrative model values; not a public performance claim.',
      footer,
    },
    {
      type: 'content', role: 'table', treatment_key: 'table', variant: 'table',
      title: 'Each workstream has an owner, proof signal, and decision date',
      subtitle: 'Editable 90-day delivery ledger',
      headers: ['Workstream', 'Owner', 'Proof signal', 'Decision'],
      rows: [
        ['Baseline sensors', 'Climate lab', '14 blocks live', 'Day 14'],
        ['Shade corridor', 'Public works', '2°C reduction', 'Day 60'],
        ['Cool-roof cohort', 'Housing team', '3°C reduction', 'Day 60'],
        ['Resident pulse', 'Community team', 'Comfort improves', 'Day 75'],
      ],
      interpretation: 'Scale only interventions that improve both measured heat and resident comfort.',
      caption: 'Synthetic owners and thresholds for an editable demonstration.',
      footer,
    },
    {
      type: 'content', role: 'decision', treatment_key: 'decision', variant: 'matrix',
      title: 'Authorize the pilot with four explicit conditions for scale',
      subtitle: 'Decision conditions and accountability',
      quadrants: [
        { title: 'Proceed', body: 'Fund fourteen-block baseline and three intervention cohorts.' },
        { title: 'Protect', body: 'Prioritize vulnerable residents and public-space access.' },
        { title: 'Measure', body: 'Track temperature, comfort, uptime, and maintenance burden.' },
        { title: 'Stop', body: 'Do not scale an intervention that misses both proof thresholds.' },
      ],
      summary_callout: 'Decision: release pilot funds now; return at day 90 with scale evidence.',
      footer,
    },
    {
      type: 'content', role: 'references', treatment_key: 'references', variant: 'table',
      table_style: 'references', title: 'Methods and sources',
      subtitle: 'Illustrative evidence register for the editable gallery',
      headers: ['ID', 'Source', 'Use'],
      rows: [
        ['S1', 'Synthetic sensor baseline', 'Heat-gap framing'],
        ['S2', 'Synthetic canopy inventory', 'Target blocks'],
        ['S3', 'Synthetic intervention model', 'Scenario comparison'],
        ['S4', 'Synthetic resident pulse', 'Comfort threshold'],
      ],
      caption: 'All values are synthetic and included only to demonstrate source-aware slide structure.',
      footer,
    },
  ];
}

async function main() {
  const args = parseArgs(process.argv);
  const pptx = new PptxGenJS();
  pptx.defineLayout({
    name: 'PPTX_SKILL_16x9',
    width: slideRenderers.SLIDE_W,
    height: slideRenderers.SLIDE_H,
  });
  pptx.layout = 'PPTX_SKILL_16x9';
  pptx.title = 'v0.9 Full-Deck Taste Grammar Gallery';
  pptx.subject = 'One urban heat topic rendered through eight editable role-layout grammars.';

  const slidesPerGrammar = roleSlides(GRAMMARS[0][2], args.adapterProof).length;
  const totalSlides = GRAMMARS.length * slidesPerGrammar;
  let slideIndex = 0;
  const manifestDecks = [];
  for (const [grammarId, presetName, grammarLabel] of GRAMMARS) {
    const contract = contractsForGrammar(grammarId, presetName);
    const deckData = {
      title: 'Cooling the Last 5 Degrees',
      metadata: { renderer_role_contracts_v2: contract },
      deck_style: { footer_page_numbers: true },
    };
    const preset = builder.applyDeckStyle(getPreset(presetName), deckData, presetName);
    const manifestSlides = [];
    for (const raw of roleSlides(grammarLabel, args.adapterProof)) {
      slideIndex += 1;
      const slideData = builder.normalizeSlide(raw, ROOT);
      slideData.__slideIndex = slideIndex;
      slideData.__slideCount = totalSlides;
      const slide = pptx.addSlide();
      builder.renderSlide(pptx, slide, slideData, preset);
      manifestSlides.push({
        role: String(raw.proof_role || raw.role),
        index: slideIndex,
        render_receipt: slideData.__renderReceipt || null,
      });
    }
    manifestDecks.push({ id: grammarId, pptx: path.resolve(args.output), slides: manifestSlides });
  }

  const output = path.resolve(args.output);
  fs.mkdirSync(path.dirname(output), { recursive: true });
  await pptx.writeFile({ fileName: output });
  if (args.manifest) {
    const manifestPath = path.resolve(args.manifest);
    fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
    fs.writeFileSync(manifestPath, JSON.stringify({
      schema_version: 'renderer-v2-adapter-proof/v1',
      source: 'scripts/build_role_contract_showcase.js',
      adapter_proof: args.adapterProof,
      decks: manifestDecks.map((deck) => ({ ...deck, pptx: output })),
      coherent_groups: Object.fromEntries(GRAMMARS.map(([grammarId]) => [grammarId, grammarId])),
    }, null, 2) + '\n');
  }
  process.stdout.write(`${output}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error && error.stack ? error.stack : error);
    process.exit(1);
  });
}
