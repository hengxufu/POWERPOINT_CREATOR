#!/usr/bin/env node
'use strict';

const assert = require('assert');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const {
  CANONICAL_ROLES,
  ROUTED_VARIANTS,
  SUPPORTED_VARIANT_ROLE_ADAPTERS,
  contractForResolvedPlan,
  resolveRenderPlan,
} = require(path.join(ROOT, 'templates', 'pptxgenjs', 'render_plan.js'));
const {
  contractsForGrammar,
} = require(path.join(ROOT, 'templates', 'pptxgenjs', 'role_layout_contracts.js'));
const builder = require(path.join(ROOT, 'scripts', 'build_deck_pptxgenjs.js'));
const slideRenderers = require(path.join(ROOT, 'templates', 'pptxgenjs', 'slides.js'));

const v2Contracts = contractsForGrammar('scientific-evidence-plate', 'lab-report');
const v1Systems = {
  schema_version: 'renderer_role_systems_v1',
  composition_grammar_id: 'scientific-evidence-plate',
};
for (const [role, contract] of Object.entries(v2Contracts.roles)) {
  const v1Role = role === 'chart' || role === 'table' ? 'data' : role;
  if (!v1Systems[`${v1Role}_system_id`]) {
    v1Systems[`${v1Role}_system_id`] = contract.fallback.system_id;
  }
}

const modes = {
  v2: {
    renderer_role_contract_version: 'renderer_role_contracts_v2',
    renderer_role_contracts_v2: v2Contracts,
    renderer_role_systems_v1: v1Systems,
    composition_grammar: 'scientific-evidence-plate',
  },
  v1: {
    renderer_role_contract_version: 'renderer_role_systems_v1',
    renderer_role_systems_v1: v1Systems,
    composition_grammar: 'scientific-evidence-plate',
  },
  legacy: {},
};

const routeInputs = [
  { type: 'title', variant: 'standard', expectedVariant: 'title' },
  { type: 'section', variant: 'standard', expectedVariant: 'section' },
  ...ROUTED_VARIANTS.map((variant) => ({
    type: 'content',
    variant,
    expectedVariant: variant === 'comparison'
      ? 'comparison-2col'
      : (['content', 'hero'].includes(variant) ? 'standard' : variant),
  })),
];

let routeCount = 0;
for (const input of routeInputs) {
  for (const role of CANONICAL_ROLES) {
    for (const [mode, preset] of Object.entries(modes)) {
      const slide = { type: input.type, variant: input.variant, role };
      const beforeSlide = JSON.stringify(slide);
      const beforePreset = JSON.stringify(preset);
      const plan = resolveRenderPlan(slide, preset);
      routeCount += 1;

      const expectedRole = input.type === 'title'
        ? 'title'
        : input.type === 'section'
          ? 'section'
          : role;
      assert.strictEqual(plan.effectiveVariant, input.expectedVariant);
      assert.strictEqual(plan.canonicalRole, expectedRole, `${input.type}/${input.variant}/${role}/${mode}`);
      assert.strictEqual(plan.roleSource, input.type === 'content' ? 'role' : 'type');
      assert.strictEqual(JSON.stringify(slide), beforeSlide, 'resolver mutated slide input');
      assert.strictEqual(JSON.stringify(preset), beforePreset, 'resolver mutated preset input');

      const pairKey = `${plan.effectiveVariant}:${plan.canonicalRole}`;
      if (mode === 'v2' && SUPPORTED_VARIANT_ROLE_ADAPTERS[pairKey]) {
        assert.strictEqual(plan.contractSource, 'v2', pairKey);
        assert.ok(plan.adapter.startsWith('v2:'));
        assert.ok(plan.contract && plan.contract.schema_version === 'renderer_role_contracts_v2');
      } else if (mode === 'legacy') {
        assert.strictEqual(plan.contractSource, 'legacy');
        assert.strictEqual(plan.contract, null);
        assert.ok(plan.fallbackReason);
      } else {
        assert.strictEqual(plan.contractSource, 'v1', `${pairKey}/${mode}`);
        assert.ok(plan.adapter.startsWith('v1:'));
        assert.ok(plan.contract && plan.contract.schema_version === 'renderer_role_systems_v1');
        assert.ok(plan.fallbackReason);
      }
    }
  }
}

const conflictCases = [
  {
    slide: { type: 'title', variant: 'chart', role: 'decision', slide_intent: 'references', treatment_key: 'table' },
    role: 'title', source: 'type', variant: 'title',
  },
  {
    slide: { type: 'section', variant: 'stats', role: 'chart' },
    role: 'section', source: 'type', variant: 'section',
  },
  {
    slide: { type: 'content', variant: 'comparison-2col', role: 'evidence', slide_intent: 'decision', treatment_key: 'chart' },
    role: 'evidence', source: 'role', variant: 'comparison-2col',
  },
  {
    slide: { type: 'content', variant: 'standard', role: 'sources', slide_intent: 'decision' },
    role: 'references', source: 'role', variant: 'standard',
  },
  {
    slide: { type: 'content', variant: 'matrix', slide_intent: 'recommendation', treatment_key: 'chart' },
    role: 'decision', source: 'slide_intent', variant: 'matrix',
  },
  {
    slide: { type: 'content', variant: 'stats', slide_intent: 'process', treatment_key: 'decision' },
    role: 'evidence', source: 'slide_intent', variant: 'stats',
  },
  {
    slide: { type: 'content', variant: 'image-sidebar', treatment_key: 'figure' },
    role: 'evidence', source: 'treatment_key', variant: 'image-sidebar',
  },
  {
    slide: { type: 'content', variant: 'chart', treatment_key: 'data' },
    role: 'chart', source: 'treatment_key', variant: 'chart',
  },
  {
    slide: { type: 'content', variant: 'standard', treatment_key: 'citation' },
    role: 'references', source: 'treatment_key', variant: 'standard',
  },
  {
    slide: { type: 'content', variant: 'table', role: 'data' },
    role: 'table', source: 'role', variant: 'table',
  },
  {
    slide: { type: 'text', variant: 'chart' },
    role: 'chart', source: 'variant_default', variant: 'chart',
  },
  {
    slide: { type: 'content', variant: 'standard', role: 'unknown-role', slide_intent: 'references', treatment_key: 'decision' },
    role: 'references', source: 'slide_intent', variant: 'standard',
  },
  {
    slide: { type: 'content', variant: 'chart', slide_intent: 'evidence' },
    role: 'chart', source: 'variant_default', variant: 'chart',
  },
  {
    slide: { type: 'content', variant: 'table', slide_intent: 'decision' },
    role: 'table', source: 'variant_default', variant: 'table',
  },
  {
    slide: { type: 'content', variant: 'table', slide_intent: 'references' },
    role: 'references', source: 'slide_intent', variant: 'table',
  },
];

for (const item of conflictCases) {
  const plan = resolveRenderPlan(item.slide, modes.v2);
  assert.strictEqual(plan.canonicalRole, item.role, JSON.stringify(item.slide));
  assert.strictEqual(plan.roleSource, item.source, JSON.stringify(item.slide));
  assert.strictEqual(plan.effectiveVariant, item.variant, JSON.stringify(item.slide));
}

const forcedRoleChecks = {
  'cards-2': ['evidence'],
  'cards-3': ['evidence'],
  timeline: ['evidence'],
  stats: ['evidence'],
  table: ['table', 'references'],
  'comparison-2col': ['comparison'],
  matrix: ['decision', 'references'],
  chart: ['chart'],
  standard: ['decision', 'references'],
};
for (const [variant, rendererRoles] of Object.entries(forcedRoleChecks)) {
  for (const canonicalRole of CANONICAL_ROLES) {
    const slide = { type: 'content', variant, role: canonicalRole };
    const plan = resolveRenderPlan(slide, modes.v2);
    slide.__renderPlan = plan;
    for (const requestedRole of rendererRoles) {
      const contract = contractForResolvedPlan(slide, modes.v2, requestedRole);
      if (requestedRole === canonicalRole && SUPPORTED_VARIANT_ROLE_ADAPTERS[`${variant}:${canonicalRole}`]) {
        assert.ok(contract, `${variant}/${canonicalRole} should expose its compatible v2 contract`);
      } else {
        assert.strictEqual(contract, null, `${variant}/${canonicalRole} silently substituted ${requestedRole}`);
      }
    }
  }
}

const pinned = resolveRenderPlan(
  { type: 'content', variant: 'chart', role: 'chart' },
  { ...modes.v2, renderer_role_contract_version: 'renderer_role_systems_v1' },
);
assert.strictEqual(pinned.contractSource, 'v1', 'explicit v1 pin was not preserved');
assert.match(pinned.fallbackReason, /explicit_v1_contract_pin/);

const unsupported = resolveRenderPlan(
  { type: 'content', variant: 'hero', role: 'decision' },
  modes.v2,
);
assert.strictEqual(unsupported.effectiveVariant, 'standard');
assert.strictEqual(unsupported.canonicalRole, 'decision');
assert.strictEqual(unsupported.contractSource, 'v2');
assert.match(unsupported.fallbackReason, /unsupported_variant:hero->standard/);

const comparisonAlias = resolveRenderPlan(
  { type: 'content', variant: 'comparison' },
  modes.v2,
);
assert.strictEqual(comparisonAlias.effectiveVariant, 'comparison-2col');
assert.strictEqual(comparisonAlias.canonicalRole, 'comparison');
assert.strictEqual(comparisonAlias.contractSource, 'v2');
assert.match(comparisonAlias.adapter, /^v2:renderComparison2col:comparison$/);

const titlePlan = resolveRenderPlan({ type: 'title', role_layout_variant: 'alternate' }, modes.v2);
assert.strictEqual(titlePlan.contractSource, 'v2');
assert.match(titlePlan.adapter, /^v2:renderTitle:title$/);
assert.strictEqual(titlePlan.contract.variant, 'alternate');

const sectionPlan = resolveRenderPlan({ type: 'section', role_layout_variant: 'dense' }, modes.v2);
assert.strictEqual(sectionPlan.contractSource, 'v2');
assert.match(sectionPlan.adapter, /^v2:renderSection:section$/);
assert.strictEqual(sectionPlan.contract.variant, 'dense');
const primarySectionPlan = resolveRenderPlan({ type: 'section', role_layout_variant: 'primary' }, modes.v2);
assert.notDeepStrictEqual(
  sectionPlan.contract.slots,
  primarySectionPlan.contract.slots,
  'dense must resolve to bounded geometry distinct from primary',
);

const alternateChart = resolveRenderPlan(
  { type: 'content', variant: 'chart', role: 'chart', role_layout_variant: 'alternate' },
  modes.v2,
);
assert.strictEqual(alternateChart.contract.variant, 'alternate');
assert.deepStrictEqual(
  alternateChart.contract.slots.chart,
  [0.08, 0, 0.84, 0.72],
  'alternate chart contract was not resolved through the bounded v2 transform',
);

function captureSlide() {
  return {
    operations: [],
    addText(text, options) { this.operations.push({ kind: 'text', text, options }); },
    addShape(shape, options) { this.operations.push({ kind: 'shape', shape, options }); },
    addImage(options) { this.operations.push({ kind: 'image', options }); },
    addNotes(notes) { this.operations.push({ kind: 'notes', notes }); },
  };
}

const alternateTitleData = {
  type: 'title',
  title: 'Slot-routed title',
  subtitle: 'The alternate contract mirrors the full title composition.',
  role_layout_variant: 'alternate',
};
alternateTitleData.__renderPlan = resolveRenderPlan(alternateTitleData, modes.v2);
const alternateTitleSlide = captureSlide();
slideRenderers.renderTitle({}, alternateTitleSlide, alternateTitleData, modes.v2);
const titleOperation = alternateTitleSlide.operations.find(
  (operation) => operation.kind === 'text' && operation.text === alternateTitleData.title,
);
assert.ok(titleOperation, 'alternate v2 title did not render its headline');
assert.ok(Math.abs(titleOperation.options.x - 3.4) < 0.001, JSON.stringify(titleOperation));
assert.ok(Math.abs(titleOperation.options.y - 1.35) < 0.001, JSON.stringify(titleOperation));
assert.ok(Math.abs(titleOperation.options.w - 5.8) < 0.001, JSON.stringify(titleOperation));

const primaryTitleData = {
  type: 'title',
  title: 'Primary slot-routed title',
  subtitle: 'Primary v2 title geometry must consume canonical slots too.',
  role_layout_variant: 'primary',
};
primaryTitleData.__renderPlan = resolveRenderPlan(primaryTitleData, modes.v2);
const primaryTitleSlide = captureSlide();
slideRenderers.renderTitle({}, primaryTitleSlide, primaryTitleData, modes.v2);
const primaryTitleOperation = primaryTitleSlide.operations.find(
  (operation) => operation.kind === 'text' && operation.text === primaryTitleData.title,
);
assert.ok(primaryTitleOperation, 'primary v2 title did not render its contract headline');
assert.ok(Math.abs(primaryTitleOperation.options.x - 0.8) < 0.001, JSON.stringify(primaryTitleOperation));
assert.ok(Math.abs(primaryTitleOperation.options.y - 1.35) < 0.001, JSON.stringify(primaryTitleOperation));
assert.ok(Math.abs(primaryTitleOperation.options.w - 5.8) < 0.001, JSON.stringify(primaryTitleOperation));

const alternateSectionData = {
  type: 'section',
  title: 'Slot-routed section',
  subtitle: 'Section geometry follows its bounded alternate contract.',
  role_layout_variant: 'alternate',
};
alternateSectionData.__renderPlan = resolveRenderPlan(alternateSectionData, modes.v2);
const alternateSectionSlide = captureSlide();
slideRenderers.renderSection({}, alternateSectionSlide, alternateSectionData, modes.v2);
const sectionOperation = alternateSectionSlide.operations.find(
  (operation) => operation.kind === 'text' && operation.text === alternateSectionData.title,
);
assert.ok(sectionOperation, 'alternate v2 section did not render its headline');
assert.ok(Math.abs(sectionOperation.options.x - 2.0) < 0.001, JSON.stringify(sectionOperation));
assert.ok(Math.abs(sectionOperation.options.y - 1.9125) < 0.001, JSON.stringify(sectionOperation));
assert.ok(Math.abs(sectionOperation.options.w - 7.2) < 0.001, JSON.stringify(sectionOperation));

const primarySectionData = {
  type: 'section',
  title: 'Primary slot-routed section',
  subtitle: 'Primary v2 section geometry must consume canonical slots too.',
  role_layout_variant: 'primary',
};
primarySectionData.__renderPlan = resolveRenderPlan(primarySectionData, modes.v2);
const primarySectionSlide = captureSlide();
slideRenderers.renderSection({}, primarySectionSlide, primarySectionData, modes.v2);
const primarySectionOperation = primarySectionSlide.operations.find(
  (operation) => operation.kind === 'text' && operation.text === primarySectionData.title,
);
assert.ok(primarySectionOperation, 'primary v2 section did not render its contract headline');
assert.ok(Math.abs(primarySectionOperation.options.x - 0.8) < 0.001, JSON.stringify(primarySectionOperation));
assert.ok(Math.abs(primarySectionOperation.options.y - 1.9125) < 0.001, JSON.stringify(primarySectionOperation));
assert.ok(Math.abs(primarySectionOperation.options.w - 7.2) < 0.001, JSON.stringify(primarySectionOperation));

const originalRenderTitle = slideRenderers.renderTitle;
const originalRenderStandard = slideRenderers.renderStandard;
const originalCallout = slideRenderers.addSummaryCallout;
const dispatched = [];
try {
  slideRenderers.renderTitle = () => dispatched.push('title');
  slideRenderers.renderStandard = () => dispatched.push('standard');
  slideRenderers.addSummaryCallout = () => dispatched.push('callout');

  const titleSlide = { type: 'title', variant: 'chart', role: 'decision' };
  builder.renderSlide({}, {}, titleSlide, modes.v2);
  assert.deepStrictEqual(dispatched.splice(0), ['title']);
  assert.strictEqual(titleSlide.__renderPlan.canonicalRole, 'title');

  const fallbackSlide = { type: 'content', variant: 'hero', role: 'decision' };
  builder.renderSlide({}, {}, fallbackSlide, modes.v2);
  assert.deepStrictEqual(dispatched.splice(0), ['standard', 'callout']);
  assert.strictEqual(fallbackSlide.__renderPlan.effectiveVariant, 'standard');
  assert.strictEqual(fallbackSlide.__renderPlan.canonicalRole, 'decision');
} finally {
  slideRenderers.renderTitle = originalRenderTitle;
  slideRenderers.renderStandard = originalRenderStandard;
  slideRenderers.addSummaryCallout = originalCallout;
}

console.log(JSON.stringify({
  passed: true,
  route_count: routeCount,
  route_inputs: routeInputs.length,
  canonical_roles: CANONICAL_ROLES.length,
  contract_modes: Object.keys(modes),
  v2_adapter_pairs: Object.keys(SUPPORTED_VARIANT_ROLE_ADAPTERS),
}, null, 2));
