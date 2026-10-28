// src/__tests__/node-exporter.test.js
//
// Tests for the Puppeteer launch-arg helper used by exportHtmlToPptx.
//
// Motivation: without --allow-file-access-from-files, Chromium blocks
// fetch() from a file:// page to other file:// URLs — which is the
// exact code path autoEmbedFonts uses to pull local .ttf files into an
// embedded font blob. The failure is silent (fetch just rejects, the
// per-font warn is easy to miss), so users end up with a fonts-less
// PPTX that PowerPoint renders in a fallback system font. Enabling the
// flag by default prevents that failure mode.

import { describe, it, expect } from 'vitest';
import JSZip from 'jszip';
import { getLaunchArgs, exportHtmlToPptx } from '../node-exporter.js';

describe('getLaunchArgs', () => {
  it('enables --allow-file-access-from-files for Chrome/Chromium/Edge', () => {
    const args = getLaunchArgs('chrome');
    expect(args).toContain('--allow-file-access-from-files');
  });

  it('keeps the existing --no-sandbox flags for Chrome-family browsers', () => {
    const args = getLaunchArgs('chrome');
    expect(args).toContain('--no-sandbox');
    expect(args).toContain('--disable-setuid-sandbox');
  });

  it('returns an empty arg list for Firefox (WebDriver BiDi manages its own launch)', () => {
    expect(getLaunchArgs('firefox')).toEqual([]);
  });

  it('is a pure function — repeated calls produce distinct arrays that can be safely mutated', () => {
    const a = getLaunchArgs('chrome');
    const b = getLaunchArgs('chrome');
    expect(a).toEqual(b);
    // Mutating one should not affect the other.
    a.push('--custom');
    expect(b).not.toContain('--custom');
  });

  it('exports slides with custom dimensions correctly', async () => {
    const html = `
      <!doctype html>
      <html>
      <body style="margin:0">
        <div class="slide" style="width:1920px;height:1080px;position:relative;background:#fff">
          <h1>Slide One</h1>
        </div>
      </body>
      </html>
    `;
    const buffer = await exportHtmlToPptx(html, {
      selector: '.slide',
      pptxOptions: {
        width: 13.333333,
        height: 7.5,
      },
    });

    const zip = await JSZip.loadAsync(buffer);
    const xml = await zip.file('ppt/presentation.xml').async('string');

    const sldSzMatch = xml.match(/<[a-zA-Z0-9:]*sldSz\s+([^>]+)>/);
    expect(sldSzMatch).not.toBeNull();
    const attrs = sldSzMatch[1];
    const cxMatch = attrs.match(/cx=["'](\d+)["']/);
    const cyMatch = attrs.match(/cy=["'](\d+)["']/);
    expect(cxMatch).not.toBeNull();
    expect(cyMatch).not.toBeNull();

    const cx = parseInt(cxMatch[1], 10);
    const cy = parseInt(cyMatch[1], 10);

    const width = cx / 914400;
    const height = cy / 914400;

    expect(width).toBeCloseTo(13.333333, 4);
    expect(height).toBeCloseTo(7.5, 4);
  }, 30000);

  it('exports pseudo-elements (linear-gradients and border triangles) correctly', async () => {
    const html = `
      <!doctype html>
      <html>
      <head>
      <style>
      body { margin: 0; }
      .slide {
        width: 1920px;
        height: 1080px;
        position: relative;
        background: #fff;
      }
      .card {
        position: absolute;
        left: 200px;
        top: 200px;
        width: 600px;
        height: 300px;
      }
      .card::before {
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        height: 12px;
        background: linear-gradient(90deg, #00479d, #1871c5);
      }
      .arrow {
        position: absolute;
        left: 950px;
        top: 350px;
        width: 180px;
        height: 6px;
      }
      .arrow::after {
        content: "";
        position: absolute;
        right: -1px;
        top: 50%;
        transform: translateY(-50%);
        width: 0;
        height: 0;
        border-left: 30px solid #ed6f18;
        border-top: 20px solid transparent;
        border-bottom: 20px solid transparent;
      }
      </style>
      </head>
      <body>
        <div class="slide">
          <div class="card"></div>
          <div class="arrow"></div>
        </div>
      </body>
      </html>
    `;
    const buffer = await exportHtmlToPptx(html, {
      selector: '.slide',
      pptxOptions: {
        includePseudoElements: true,
      },
    });

    const zip = await JSZip.loadAsync(buffer);
    const mediaFiles = Object.keys(zip.files).filter(k => k.startsWith('ppt/media/'));
    expect(mediaFiles.length).toBeGreaterThanOrEqual(2);
  }, 40000);
});
