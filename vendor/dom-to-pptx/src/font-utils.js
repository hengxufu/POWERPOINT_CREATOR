// src/font-utils.js
import { Font, woff2 } from 'fonteditor-core';
import pako from 'pako';
import { woff2WasmBase64 } from './woff2-wasm-base64.js';

let isWoff2Inited = false;

/**
 * Converts various font formats to EOT (Embedded OpenType),
 * which is highly compatible with PowerPoint embedding.
 * Supports merging multiple subsets (e.g. from Google Fonts split ranges).
 * @param {string|Array<Object>} typeOrSubsets - 'ttf', 'woff', 'woff2', 'otf' OR array of {type, buffer}
 * @param {ArrayBuffer|string} [fontBufferOrWasmUrl] - The raw font data (or wasmUrl if subsets array is passed)
 * @param {string} [wasmUrl] - Custom URL for woff2.wasm
 */
export async function fontToEot(typeOrSubsets, fontBufferOrWasmUrl, wasmUrl) {
  let subsets;
  let actualWasmUrl = wasmUrl;

  if (Array.isArray(typeOrSubsets)) {
    subsets = typeOrSubsets;
    actualWasmUrl = fontBufferOrWasmUrl;
  } else {
    subsets = [{ type: typeOrSubsets, buffer: fontBufferOrWasmUrl }];
  }

  if (subsets.length === 0) {
    throw new Error('No font buffers provided to convert.');
  }

  const hasWoff2 = subsets.some((s) => s.type === 'woff2');
  if (hasWoff2 && !isWoff2Inited) {
    const defaultWasmUrl = typeof window !== 'undefined' ? woff2WasmBase64 : undefined;
    await woff2.init(actualWasmUrl || defaultWasmUrl);
    isWoff2Inited = true;
  }

  const fonts = subsets.map((s) => {
    const options = {
      type: s.type,
      hinting: true,
      compound2simple: true,
      // inflate is required for WOFF decoding
      inflate: s.type === 'woff' ? pako.inflate : undefined,
    };
    const f = Font.create(s.buffer, options);
    f.compound2simple();
    return f;
  });

  const baseFont = fonts[0];
  for (let i = 1; i < fonts.length; i++) {
    baseFont.merge(fonts[i], { scale: 1 });
  }

  // Deduplicate glyfs by unicode to avoid "Repeat unicode" errors when writing to EOT
  const fontObject = baseFont.get();
  if (fontObject.glyf && fontObject.glyf.length > 0) {
    const seenUnicodes = new Set();
    const cleanGlyfs = [];

    // Always keep the first (.notdef) glyph
    cleanGlyfs.push(fontObject.glyf[0]);
    if (fontObject.glyf[0].unicode) {
      fontObject.glyf[0].unicode.forEach((u) => seenUnicodes.add(u));
    }

    for (let i = 1; i < fontObject.glyf.length; i++) {
      const glyf = fontObject.glyf[i];
      if (glyf.unicode && glyf.unicode.length > 0) {
        const remainingUnicodes = glyf.unicode.filter((u) => !seenUnicodes.has(u));
        if (remainingUnicodes.length > 0) {
          glyf.unicode = remainingUnicodes;
          remainingUnicodes.forEach((u) => seenUnicodes.add(u));
          cleanGlyfs.push(glyf);
        }
      } else {
        cleanGlyfs.push(glyf);
      }
    }
    fontObject.glyf = cleanGlyfs;
    baseFont.set(fontObject);
  }

  const eotBuffer = baseFont.write({
    type: 'eot',
    toBuffer: true,
  });

  if (eotBuffer instanceof ArrayBuffer) {
    return eotBuffer;
  }

  // Ensure we return an ArrayBuffer
  return eotBuffer.buffer.slice(eotBuffer.byteOffset, eotBuffer.byteOffset + eotBuffer.byteLength);
}
