// src/__tests__/font-detection.test.js
//
// Tests for the font-detection helpers in src/utils.js — extracted from
// the exportToPptx pipeline so they can be exercised in isolation:
//
//   - getFontsFromStyleSheets: scans an array of CSSStyleSheet-like
//     objects (including @import chains) for @font-face declarations
//     matching the requested families.
//   - classifyFontVariant: maps CSS font-weight / font-style into one of
//     PowerPoint's four embedded-font slots.
//   - detectVariantSlotCollisions: flags when multiple weights of the
//     same family collapse into the same slot (e.g. weight 700 + 900
//     both landing in `bold`).
//
// The @import traversal test in particular covers a real user-hit
// footgun: `@import url('./fonts.css')` in a theme file used to escape
// auto-embed discovery and silently produce a fonts-less PPTX.

import { describe, it, expect } from 'vitest';
import {
  getFontsFromStyleSheets,
  classifyFontVariant,
  detectVariantSlotCollisions,
  resolveCssUrl,
  parseImportUrlsFromCssText,
  parseFontFacesFromCssText,
} from '../utils.js';

// -- Helpers to build CSSStyleSheet-like fixtures without a real DOM ----------

function fontFaceRule({ family, src, weight = '400', style = 'normal' }) {
  return {
    constructor: { name: 'CSSFontFaceRule' },
    style: {
      getPropertyValue: (prop) => {
        if (prop === 'font-family') return `"${family}"`;
        if (prop === 'src') return src;
        if (prop === 'font-weight') return String(weight);
        if (prop === 'font-style') return style;
        return '';
      },
    },
  };
}

function importRule(importedSheet) {
  return {
    constructor: { name: 'CSSImportRule' },
    styleSheet: importedSheet,
  };
}

function makeSheet(rules) {
  return { cssRules: rules };
}

// -----------------------------------------------------------------------------

describe('getFontsFromStyleSheets', () => {
  it('discovers @font-face rules for families in usedFamilies', () => {
    const sheet = makeSheet([
      fontFaceRule({ family: 'Inter', src: "url('fonts/Inter-Regular.ttf')", weight: '400' }),
      fontFaceRule({ family: 'Merriweather', src: "url('fonts/Merri.ttf')", weight: '400' }),
    ]);

    const used = new Set(['Inter']);
    const found = getFontsFromStyleSheets(used, [sheet]);
    expect(found).toHaveLength(1);
    expect(found[0].name).toBe('Inter');
    expect(found[0].url).toBe('fonts/Inter-Regular.ttf');
  });

  it('resolves relative src URLs against the stylesheet href, not the document base', () => {
    // Fixture: an external stylesheet at /assets/deck.css declares
    // src: url('fonts/Inter-Regular.ttf'). The browser resolves that URL
    // relative to the stylesheet when rendering, but fetch() during embedding
    // resolves it against the document — so without href-based resolution the
    // font 404s and auto-embed silently falls back to a system font.
    const sheet = makeSheet([
      fontFaceRule({ family: 'Inter', src: "url('fonts/Inter-Regular.ttf')", weight: '400' }),
    ]);
    sheet.href = 'https://example.com/assets/deck.css';

    const found = getFontsFromStyleSheets(new Set(['Inter']), [sheet]);
    expect(found).toHaveLength(1);
    expect(found[0].url).toBe('https://example.com/assets/fonts/Inter-Regular.ttf');
  });

  it('leaves relative src URLs untouched for hrefless (inline <style>) sheets', () => {
    const sheet = makeSheet([
      fontFaceRule({ family: 'Inter', src: "url('fonts/Inter-Regular.ttf')", weight: '400' }),
    ]);

    const found = getFontsFromStyleSheets(new Set(['Inter']), [sheet]);
    expect(found).toHaveLength(1);
    expect(found[0].url).toBe('fonts/Inter-Regular.ttf');
  });

  it('recurses into @import chains — the common `theme.css imports fonts.css` pattern', () => {
    // Fixture: `fonts.css` (imported) declares @font-face for Inter Regular + Bold.
    // `theme.css` (top-level) contains only an @import pointing at fonts.css.
    // Before this fix, top-level scanning of `theme.css` found zero @font-face
    // rules and auto-embed produced a fonts-less PPTX (~15 KB instead of ~300 KB).
    const importedSheet = makeSheet([
      fontFaceRule({ family: 'Inter', src: "url('fonts/Inter-Regular.ttf')", weight: '400' }),
      fontFaceRule({ family: 'Inter', src: "url('fonts/Inter-Bold.ttf')", weight: '700' }),
    ]);
    const topSheet = makeSheet([importRule(importedSheet)]);

    const used = new Set(['Inter']);
    const found = getFontsFromStyleSheets(used, [topSheet]);
    expect(found).toHaveLength(2);
    const weights = found.map((f) => f.weight).sort();
    expect(weights).toEqual(['400', '700']);
  });

  it('recurses through multiple levels of @import', () => {
    // A imports B, B imports C, C declares the actual @font-face.
    const level3 = makeSheet([
      fontFaceRule({ family: 'Inter', src: "url('a.ttf')", weight: '400' }),
    ]);
    const level2 = makeSheet([importRule(level3)]);
    const level1 = makeSheet([importRule(level2)]);

    const found = getFontsFromStyleSheets(new Set(['Inter']), [level1]);
    expect(found).toHaveLength(1);
    expect(found[0].url).toBe('a.ttf');
  });

  it('does not loop forever on cyclic @import graphs', () => {
    // Pathological but survivable: sheet A imports sheet B; sheet B
    // imports sheet A back. Should terminate rather than stack-overflow.
    const a = makeSheet([]);
    const b = makeSheet([importRule(a)]);
    a.cssRules = [
      importRule(b),
      fontFaceRule({ family: 'Inter', src: "url('cyclic.ttf')" }),
    ];

    const found = getFontsFromStyleSheets(new Set(['Inter']), [a]);
    expect(found).toHaveLength(1);
    expect(found[0].url).toBe('cyclic.ttf');
  });

  it('deduplicates by URL across multiple sheets', () => {
    const sheetA = makeSheet([
      fontFaceRule({ family: 'Inter', src: "url('inter.ttf')", weight: '400' }),
    ]);
    const sheetB = makeSheet([
      fontFaceRule({ family: 'Inter', src: "url('inter.ttf')", weight: '400' }),
    ]);
    const found = getFontsFromStyleSheets(new Set(['Inter']), [sheetA, sheetB]);
    expect(found).toHaveLength(1);
  });

  it('preserves font-weight and font-style on each detected entry', () => {
    const sheet = makeSheet([
      fontFaceRule({ family: 'Inter', src: "url('a.ttf')", weight: '400', style: 'normal' }),
      fontFaceRule({ family: 'Inter', src: "url('b.ttf')", weight: '700', style: 'italic' }),
    ]);
    const found = getFontsFromStyleSheets(new Set(['Inter']), [sheet]);
    expect(found).toHaveLength(2);
    const regular = found.find((f) => f.url === 'a.ttf');
    const boldItalic = found.find((f) => f.url === 'b.ttf');
    expect(regular).toMatchObject({ weight: '400', style: 'normal' });
    expect(boldItalic).toMatchObject({ weight: '700', style: 'italic' });
  });

  it('survives a stylesheet that throws on cssRules access (cross-origin)', () => {
    // Simulates the SecurityError thrown by cross-origin sheets (e.g.
    // Google Fonts CSS without CORS headers). The scan should continue
    // on to other sheets rather than propagating the exception.
    const hostileSheet = {
      href: 'https://example.com/blocked.css',
      get cssRules() {
        throw new Error('SecurityError: cross-origin');
      },
    };
    const okSheet = makeSheet([
      fontFaceRule({ family: 'Inter', src: "url('local.ttf')", weight: '400' }),
    ]);

    expect(() =>
      getFontsFromStyleSheets(new Set(['Inter']), [hostileSheet, okSheet])
    ).not.toThrow();
    const found = getFontsFromStyleSheets(new Set(['Inter']), [hostileSheet, okSheet]);
    expect(found).toHaveLength(1);
    expect(found[0].url).toBe('local.ttf');
  });
});

describe('classifyFontVariant', () => {
  it('maps numeric weights to bold/regular based on the 600 threshold', () => {
    expect(classifyFontVariant(400, 'normal')).toBe('regular');
    expect(classifyFontVariant(500, 'normal')).toBe('regular'); // Medium is not bold
    expect(classifyFontVariant(600, 'normal')).toBe('bold'); // SemiBold rounds up
    expect(classifyFontVariant(700, 'normal')).toBe('bold');
    expect(classifyFontVariant(900, 'normal')).toBe('bold'); // Black collapses into bold slot
  });

  it('handles the keyword weights (bold, bolder, lighter, normal)', () => {
    expect(classifyFontVariant('bold', 'normal')).toBe('bold');
    expect(classifyFontVariant('bolder', 'normal')).toBe('bold');
    expect(classifyFontVariant('lighter', 'normal')).toBe('regular');
    expect(classifyFontVariant('normal', 'normal')).toBe('regular');
  });

  it('classifies italic and oblique into italic slots', () => {
    expect(classifyFontVariant(400, 'italic')).toBe('italic');
    expect(classifyFontVariant(400, 'oblique')).toBe('italic');
    expect(classifyFontVariant(700, 'italic')).toBe('boldItalic');
  });

  it('defaults to regular for missing / undefined inputs', () => {
    expect(classifyFontVariant(undefined, undefined)).toBe('regular');
    expect(classifyFontVariant(null, null)).toBe('regular');
    expect(classifyFontVariant('', '')).toBe('regular');
  });

  it('handles nonsense weights by falling back to 400', () => {
    expect(classifyFontVariant('mystery', 'normal')).toBe('regular');
  });
});

describe('detectVariantSlotCollisions', () => {
  it('reports weight 700 + weight 900 for same family as a bold-slot collision', () => {
    // The workflow-relevant case: Inter Bold + Inter Black both classify
    // as `bold`. Black glyphs silently get merged into Bold's slot.
    const entries = [
      { name: 'Inter', weight: 400, style: 'normal' },
      { name: 'Inter', weight: 700, style: 'normal' },
      { name: 'Inter', weight: 900, style: 'normal' },
    ];
    const collisions = detectVariantSlotCollisions(entries);
    expect(collisions).toHaveLength(1);
    expect(collisions[0].family).toBe('Inter');
    expect(collisions[0].variant).toBe('bold');
    expect(collisions[0].weights).toEqual(['700', '900']);
  });

  it('does not report a collision when weights land in different slots', () => {
    const entries = [
      { name: 'Inter', weight: 400, style: 'normal' },
      { name: 'Inter', weight: 700, style: 'normal' },
    ];
    expect(detectVariantSlotCollisions(entries)).toEqual([]);
  });

  it('separates collisions per family', () => {
    const entries = [
      { name: 'Inter', weight: 700, style: 'normal' },
      { name: 'Inter', weight: 900, style: 'normal' },
      { name: 'Merriweather', weight: 800, style: 'italic' },
      { name: 'Merriweather', weight: 900, style: 'italic' },
    ];
    const collisions = detectVariantSlotCollisions(entries);
    expect(collisions).toHaveLength(2);
    const families = collisions.map((c) => c.family).sort();
    expect(families).toEqual(['Inter', 'Merriweather']);
  });

  it('does not report a spurious collision when the same weight appears twice', () => {
    // Two @font-face rules at weight 400 for the same family (e.g.
    // pointing at Latin vs Cyrillic subsets) should NOT trigger the
    // collision warning — same weight, no distinct face is being lost.
    const entries = [
      { name: 'Inter', weight: 400, style: 'normal' },
      { name: 'Inter', weight: 400, style: 'normal' },
    ];
    expect(detectVariantSlotCollisions(entries)).toEqual([]);
  });
});

describe('resolveCssUrl', () => {
  it('resolves relative URL against an absolute base URL', () => {
    expect(resolveCssUrl('fonts/font.woff2', 'https://example.com/css/main.css')).toBe(
      'https://example.com/css/fonts/font.woff2'
    );
  });

  it('safely resolves relative URL when rawBase is itself relative (e.g., assets/deck.css in jsdom)', () => {
    const resolved = resolveCssUrl('fonts/font.woff2', 'assets/deck.css');
    expect(resolved).toBeTruthy();
    expect(resolved).toContain('/assets/fonts/font.woff2');
  });

  it('returns original URL gracefully on invalid/empty inputs', () => {
    expect(resolveCssUrl('', 'https://example.com')).toBe('');
    expect(resolveCssUrl('font.ttf', null)).toBe('font.ttf');
    expect(resolveCssUrl('font.ttf', undefined)).toBe('font.ttf');
  });
});

describe('parseImportUrlsFromCssText', () => {
  it('extracts and resolves @import with url() using double, single, and no quotes', () => {
    const css = `
      @import url("theme.css");
      @import url('fonts/sub.css');
      @import url(plain.css);
    `;
    const urls = parseImportUrlsFromCssText(css, 'https://example.com/assets/style.css');
    expect(urls).toEqual([
      'https://example.com/assets/theme.css',
      'https://example.com/assets/fonts/sub.css',
      'https://example.com/assets/plain.css',
    ]);
  });

  it('extracts and resolves bare string @import statements', () => {
    const css = `
      @import "base.css";
      @import 'vendor.css';
    `;
    const urls = parseImportUrlsFromCssText(css, 'https://example.com/style.css');
    expect(urls).toEqual([
      'https://example.com/base.css',
      'https://example.com/vendor.css',
    ]);
  });

  it('deduplicates identical import targets', () => {
    const css = `
      @import url("common.css");
      @import "common.css";
    `;
    const urls = parseImportUrlsFromCssText(css, 'https://example.com/');
    expect(urls).toHaveLength(1);
    expect(urls[0]).toBe('https://example.com/common.css');
  });
});

describe('parseFontFacesFromCssText with relative baseHref', () => {
  it('resolves font URLs against relative baseHref without throwing TypeError', () => {
    const css = `
      @font-face {
        font-family: 'RelativeFont';
        src: url('../fonts/rel.woff2') format('woff2');
      }
    `;
    const fonts = parseFontFacesFromCssText(css, new Set(['RelativeFont']), 'themes/dark/theme.css');
    expect(fonts).toHaveLength(1);
    expect(fonts[0].url).toContain('/themes/fonts/rel.woff2');
  });
});
