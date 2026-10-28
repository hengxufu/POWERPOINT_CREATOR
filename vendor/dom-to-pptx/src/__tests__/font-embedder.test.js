// src/__tests__/font-embedder.test.js
//
// Tests for PPTXEmbedFonts.updatePresentationXML — specifically that
// multiple @font-face variants for the same family (Regular, Bold, etc.)
// each get their own slot in <p:embeddedFontLst>. Before the fix, the
// method walked this.fonts and short-circuited on the first entry that
// matched a given typeface, so a Bold font added after a Regular one
// under the same family name was silently dropped and PowerPoint had to
// synthesise fake-bold from Regular glyphs.
//
// We push directly to embedder.fonts here rather than going through
// addFont() so we do not need real font buffers (addFont() runs the data
// through fontToEot / opentype.js). The XML emit is the code path with
// the bug, and it is fully exercised without any font conversion.

import { describe, it, expect } from 'vitest';
import JSZip from 'jszip';
import { PPTXEmbedFonts } from '../font-embedder.js';

const P_NS = 'http://schemas.openxmlformats.org/presentationml/2006/main';

function buildMinimalPresentationZip() {
  const zip = new JSZip();
  zip.file(
    'ppt/presentation.xml',
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="${P_NS}"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:defaultTextStyle/>
</p:presentation>`
  );
  return zip;
}

async function embeddedFontLstFromZip(zip) {
  const xml = await zip.file('ppt/presentation.xml').async('string');
  const doc = new DOMParser().parseFromString(xml, 'text/xml');
  return doc.getElementsByTagName('p:embeddedFontLst')[0] || null;
}

describe('PPTXEmbedFonts.updatePresentationXML', () => {
  it('emits one <p:embeddedFont> per family with a child element per declared variant', async () => {
    const zip = buildMinimalPresentationZip();
    const embedder = new PPTXEmbedFonts();
    await embedder.loadZip(zip);

    // Two variants for the same family plus one variant for a second family.
    embedder.fonts = [
      { name: 'Inter', variant: 'regular', data: new Uint8Array(0), rid: 201314 },
      { name: 'Inter', variant: 'bold', data: new Uint8Array(0), rid: 201315 },
      { name: 'Merriweather', variant: 'italic', data: new Uint8Array(0), rid: 201316 },
    ];

    await embedder.updatePresentationXML();

    const embeddedFontLst = await embeddedFontLstFromZip(zip);
    expect(embeddedFontLst).not.toBeNull();

    const embeddedFonts = Array.from(embeddedFontLst.getElementsByTagName('p:embeddedFont'));
    expect(embeddedFonts).toHaveLength(2);

    const inter = embeddedFonts.find(
      (n) => n.getElementsByTagName('p:font')[0].getAttribute('typeface') === 'Inter'
    );
    expect(inter).toBeTruthy();
    expect(inter.getElementsByTagName('p:regular')).toHaveLength(1);
    expect(inter.getElementsByTagName('p:bold')).toHaveLength(1);
    expect(inter.getElementsByTagName('p:italic')).toHaveLength(0);
    expect(inter.getElementsByTagName('p:boldItalic')).toHaveLength(0);
    expect(inter.getElementsByTagName('p:regular')[0].getAttribute('r:id')).toBe('rId201314');
    expect(inter.getElementsByTagName('p:bold')[0].getAttribute('r:id')).toBe('rId201315');

    const merri = embeddedFonts.find(
      (n) => n.getElementsByTagName('p:font')[0].getAttribute('typeface') === 'Merriweather'
    );
    expect(merri).toBeTruthy();
    expect(merri.getElementsByTagName('p:italic')).toHaveLength(1);
    expect(merri.getElementsByTagName('p:regular')).toHaveLength(0);
    expect(merri.getElementsByTagName('p:italic')[0].getAttribute('r:id')).toBe('rId201316');
  });

  it('defaults to the regular slot when a font has no variant field (backward compatible)', async () => {
    const zip = buildMinimalPresentationZip();
    const embedder = new PPTXEmbedFonts();
    await embedder.loadZip(zip);

    // Old-style entries with no variant should still land in <p:regular>.
    embedder.fonts = [{ name: 'LegacyFont', data: new Uint8Array(0), rid: 201314 }];

    await embedder.updatePresentationXML();

    const embeddedFontLst = await embeddedFontLstFromZip(zip);
    const embeddedFonts = Array.from(embeddedFontLst.getElementsByTagName('p:embeddedFont'));
    expect(embeddedFonts).toHaveLength(1);
    expect(embeddedFonts[0].getElementsByTagName('p:regular')).toHaveLength(1);
    expect(embeddedFonts[0].getElementsByTagName('p:bold')).toHaveLength(0);
  });

  it('does not duplicate an existing <p:embeddedFont> entry on repeat calls', async () => {
    const zip = buildMinimalPresentationZip();
    const embedder = new PPTXEmbedFonts();
    await embedder.loadZip(zip);

    embedder.fonts = [
      { name: 'Inter', variant: 'regular', data: new Uint8Array(0), rid: 201314 },
      { name: 'Inter', variant: 'bold', data: new Uint8Array(0), rid: 201315 },
    ];

    await embedder.updatePresentationXML();
    await embedder.updatePresentationXML();

    const embeddedFontLst = await embeddedFontLstFromZip(zip);
    const interBlocks = Array.from(embeddedFontLst.getElementsByTagName('p:embeddedFont')).filter(
      (n) => n.getElementsByTagName('p:font')[0].getAttribute('typeface') === 'Inter'
    );
    expect(interBlocks).toHaveLength(1);
  });
});
