// src/__tests__/speaker-notes.test.js
//
// Tests for extractSpeakerNotesFromElement, the helper that reads
// PowerPoint speaker-notes text from a slide's DOM. The extractor scans
// for elements with a `data-pptx-notes` attribute and returns their
// text content joined with blank-line separators.
//
// This is the feature that removes the need for a separate
// python-pptx post-process step to populate speaker notes on decks
// built with dom-to-pptx.

import { describe, it, expect } from 'vitest';
import { extractSpeakerNotesFromElement } from '../utils.js';

// jsdom provides `document.createElement` etc. under vitest's default
// environment. All helpers below build real DOM subtrees.

function slideWith(html) {
  const div = document.createElement('div');
  div.innerHTML = html;
  return div;
}

describe('extractSpeakerNotesFromElement', () => {
  it('extracts text content from an element carrying data-pptx-notes', () => {
    const root = slideWith(`
      <h1>Slide headline</h1>
      <div data-pptx-notes hidden>Welcome to the deck. Say hello.</div>
    `);
    expect(extractSpeakerNotesFromElement(root)).toBe('Welcome to the deck. Say hello.');
  });

  it('reads from <template>.content, not .textContent', () => {
    // <template> is the recommended container: its markup is inert, so
    // the notes never render on-slide. jsdom stores template contents in
    // a DocumentFragment on `.content`.
    const root = slideWith(`
      <h1>Slide headline</h1>
      <template data-pptx-notes>Notes inside a template.</template>
    `);
    expect(extractSpeakerNotesFromElement(root)).toBe('Notes inside a template.');
  });

  it('concatenates multiple annotated elements with a blank line between them', () => {
    const root = slideWith(`
      <p data-pptx-notes>First note.</p>
      <h1>Some visible content</h1>
      <p data-pptx-notes>Second note.</p>
    `);
    expect(extractSpeakerNotesFromElement(root)).toBe('First note.\n\nSecond note.');
  });

  it('preserves the document order of annotated elements', () => {
    const root = slideWith(`
      <p data-pptx-notes>A</p>
      <p data-pptx-notes>B</p>
      <p data-pptx-notes>C</p>
    `);
    expect(extractSpeakerNotesFromElement(root)).toBe('A\n\nB\n\nC');
  });

  it('returns empty string when no elements carry the attribute', () => {
    const root = slideWith(`
      <h1>Slide headline</h1>
      <p>Body text.</p>
    `);
    expect(extractSpeakerNotesFromElement(root)).toBe('');
  });

  it('ignores annotated elements with no text content', () => {
    const root = slideWith(`
      <template data-pptx-notes></template>
      <p data-pptx-notes>Real note.</p>
      <div data-pptx-notes>   </div>
    `);
    expect(extractSpeakerNotesFromElement(root)).toBe('Real note.');
  });

  it('trims leading and trailing whitespace on each note fragment', () => {
    const root = slideWith(`
      <template data-pptx-notes>
        Multi-line notes.
        With indentation.
      </template>
    `);
    // Leading/trailing whitespace on the fragment gets trimmed by the
    // extractor; interior whitespace is preserved verbatim.
    const result = extractSpeakerNotesFromElement(root);
    expect(result.startsWith('Multi-line notes.')).toBe(true);
    expect(result.endsWith('With indentation.')).toBe(true);
  });

  it('returns empty string when the root is null or missing querySelectorAll', () => {
    expect(extractSpeakerNotesFromElement(null)).toBe('');
    expect(extractSpeakerNotesFromElement(undefined)).toBe('');
    expect(extractSpeakerNotesFromElement({})).toBe('');
  });

  it('reads notes from elements at arbitrary depth in the slide subtree', () => {
    const root = slideWith(`
      <section>
        <article>
          <footer>
            <template data-pptx-notes>Deeply nested note.</template>
          </footer>
        </article>
      </section>
    `);
    expect(extractSpeakerNotesFromElement(root)).toBe('Deeply nested note.');
  });

  it('works with any element type (attribute-driven, not tag-driven)', () => {
    const root = slideWith(`
      <aside data-pptx-notes>Sidebar note.</aside>
    `);
    expect(extractSpeakerNotesFromElement(root)).toBe('Sidebar note.');
  });
});
