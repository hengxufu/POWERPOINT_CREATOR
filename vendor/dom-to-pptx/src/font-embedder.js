// src/font-embedder.js
import opentype from 'opentype.js';
import { fontToEot } from './font-utils.js';

const START_RID = 201314;

const P_NS = 'http://schemas.openxmlformats.org/presentationml/2006/main';
const R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships';
const CONTENT_TYPES_NS = 'http://schemas.openxmlformats.org/package/2006/content-types';
const RELS_NS = 'http://schemas.openxmlformats.org/package/2006/relationships';

export class PPTXEmbedFonts {
  constructor() {
    this.zip = null;
    this.rId = START_RID;
    this.fonts = []; // { name, data, rid }
  }

  async loadZip(zip) {
    this.zip = zip;
  }

  /**
   * Reads the font name from the buffer using opentype.js
   */
  getFontInfo(fontBuffer) {
    try {
      const font = opentype.parse(fontBuffer);
      const names = font.names;
      // Prefer English name, fallback to others
      const fontFamily = names.fontFamily.en || Object.values(names.fontFamily)[0];
      return { name: fontFamily };
    } catch (e) {
      console.warn('Could not parse font info', e);
      return { name: 'Unknown' };
    }
  }

  async addFont(fontFace, source, typeOrWasmUrl, wasmUrl, variant) {
    // Convert to EOT/fntdata for PPTX compatibility
    let eotData;
    if (Array.isArray(source)) {
      eotData = await fontToEot(source, typeOrWasmUrl);
    } else {
      eotData = await fontToEot(typeOrWasmUrl, source, wasmUrl);
    }
    const rid = this.rId++;
    // variant is one of: regular, bold, italic, boldItalic (PowerPoint's
    // four embedded-font slots). Default to regular for callers that do
    // not supply one, preserving the previous single-slot behaviour.
    this.fonts.push({ name: fontFace, variant: variant || 'regular', data: eotData, rid });
  }

  async updateFiles() {
    await this.updateContentTypesXML();
    await this.updatePresentationXML();
    await this.updateRelsPresentationXML();
    this.updateFontFiles();
  }

  async generateBlob() {
    if (!this.zip) throw new Error('Zip not loaded');
    return this.zip.generateAsync({
      type: 'blob',
      compression: 'DEFLATE',
      compressionOptions: { level: 6 },
    });
  }

  // --- XML Manipulation Methods ---

  async updateContentTypesXML() {
    const file = this.zip.file('[Content_Types].xml');
    if (!file) throw new Error('[Content_Types].xml not found');

    const xmlStr = await file.async('string');
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlStr, 'text/xml');

    const types = doc.getElementsByTagName('Types')[0];
    const defaults = Array.from(doc.getElementsByTagName('Default'));

    const hasFntData = defaults.some((el) => el.getAttribute('Extension') === 'fntdata');

    if (!hasFntData) {
      const el = doc.createElementNS(CONTENT_TYPES_NS, 'Default');
      el.setAttribute('Extension', 'fntdata');
      el.setAttribute('ContentType', 'application/x-fontdata');
      types.insertBefore(el, types.firstChild);
    }

    this.zip.file('[Content_Types].xml', new XMLSerializer().serializeToString(doc));
  }

  async updatePresentationXML() {
    const file = this.zip.file('ppt/presentation.xml');
    if (!file) throw new Error('ppt/presentation.xml not found');

    const xmlStr = await file.async('string');
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlStr, 'text/xml');
    const presentation = doc.getElementsByTagName('p:presentation')[0];

    // Enable embedding flags
    presentation.setAttribute('saveSubsetFonts', 'true');
    presentation.setAttribute('embedTrueTypeFonts', 'true');

    // Find or create embeddedFontLst
    let embeddedFontLst = presentation.getElementsByTagName('p:embeddedFontLst')[0];

    if (!embeddedFontLst) {
      embeddedFontLst = doc.createElementNS(P_NS, 'p:embeddedFontLst');

      // Insert before defaultTextStyle or at end
      const defaultTextStyle =
        presentation.getElementsByTagName('p:defaultTextStyle')[0] ||
        presentation.getElementsByTagNameNS(P_NS, 'defaultTextStyle')[0];
      if (defaultTextStyle) {
        presentation.insertBefore(embeddedFontLst, defaultTextStyle);
      } else {
        presentation.appendChild(embeddedFontLst);
      }
    }

    // Group added fonts by typeface so we can emit one <p:embeddedFont>
    // block per family with the right variant children. PowerPoint's
    // embedded-font model supports four slots per family: regular, bold,
    // italic, boldItalic. Emitting only <p:regular> when Bold was declared
    // causes PowerPoint to fall back to synthesising bold from the Regular
    // glyphs, which renders visibly differently from real Bold.
    const byName = new Map();
    this.fonts.forEach((font) => {
      if (!byName.has(font.name)) byName.set(font.name, []);
      byName.get(font.name).push(font);
    });

    const variantOrder = ['regular', 'bold', 'italic', 'boldItalic'];

    byName.forEach((variants, name) => {
      const alreadyDeclared =
        Array.from(embeddedFontLst.getElementsByTagNameNS(P_NS, 'font')).find(
          (node) => node.getAttribute('typeface') === name
        ) ||
        Array.from(embeddedFontLst.getElementsByTagName('p:font')).find(
          (node) => node.getAttribute('typeface') === name
        );
      if (alreadyDeclared) return;

      const embedFont = doc.createElementNS(P_NS, 'p:embeddedFont');
      const fontNode = doc.createElementNS(P_NS, 'p:font');
      fontNode.setAttribute('typeface', name);
      embedFont.appendChild(fontNode);

      for (const variantName of variantOrder) {
        const font = variants.find((v) => (v.variant || 'regular') === variantName);
        if (font) {
          const el = doc.createElementNS(P_NS, 'p:' + variantName);
          el.setAttributeNS(R_NS, 'r:id', 'rId' + font.rid);
          embedFont.appendChild(el);
        }
      }

      embeddedFontLst.appendChild(embedFont);
    });

    this.zip.file('ppt/presentation.xml', new XMLSerializer().serializeToString(doc));
  }

  async updateRelsPresentationXML() {
    const file = this.zip.file('ppt/_rels/presentation.xml.rels');
    if (!file) throw new Error('presentation.xml.rels not found');

    const xmlStr = await file.async('string');
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlStr, 'text/xml');
    const relationships = doc.getElementsByTagName('Relationships')[0];

    this.fonts.forEach((font) => {
      const rel = doc.createElementNS(RELS_NS, 'Relationship');
      rel.setAttribute('Id', `rId${font.rid}`);
      rel.setAttribute('Target', `fonts/${font.rid}.fntdata`);
      rel.setAttribute('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/font');
      relationships.appendChild(rel);
    });

    this.zip.file('ppt/_rels/presentation.xml.rels', new XMLSerializer().serializeToString(doc));
  }

  updateFontFiles() {
    this.fonts.forEach((font) => {
      this.zip.file(`ppt/fonts/${font.rid}.fntdata`, font.data);
    });
  }
}
