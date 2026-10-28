import { describe, it, expect } from 'vitest';
import { splitPreformattedText } from '../utils.js';

const texts = (segs) => segs.map((s) => s.text);
const breaks = (segs) => segs.map((s) => s.breakLine);

describe('splitPreformattedText', () => {
  it('preserves newlines as hard breaks (pre)', () => {
    const segs = splitPreformattedText('line1\nline2\nline3', 'pre', { isLastChild: true });
    expect(texts(segs)).toEqual(['line1', 'line2', 'line3']);
    expect(breaks(segs)).toEqual([true, true, false]);
  });

  it('preserves leading indentation and inner spaces for pre / pre-wrap', () => {
    expect(texts(splitPreformattedText('  a   b', 'pre', { isLastChild: true }))).toEqual(['  a   b']);
    expect(texts(splitPreformattedText('  a   b', 'pre-wrap', { isLastChild: true }))).toEqual(['  a   b']);
  });

  it('collapses runs of spaces/tabs but keeps newlines for pre-line', () => {
    const segs = splitPreformattedText('a\t \tb\n  c', 'pre-line', { isLastChild: true });
    expect(texts(segs)).toEqual(['a b', ' c']);
    expect(breaks(segs)).toEqual([true, false]);
  });

  it('renders tabs as spaces for pre (no PPTX tab stops)', () => {
    expect(texts(splitPreformattedText('\tx', 'pre', { isLastChild: true }))).toEqual(['    x']);
  });

  it('keeps internal blank lines', () => {
    const segs = splitPreformattedText('a\n\nb', 'pre', { isLastChild: true });
    expect(texts(segs)).toEqual(['a', '', 'b']);
    expect(breaks(segs)).toEqual([true, true, false]);
  });

  it('ignores a single newline immediately after a <pre> start tag', () => {
    const segs = splitPreformattedText('\nfirst\nsecond', 'pre', {
      isFirstChild: true,
      isPre: true,
      isLastChild: true,
    });
    expect(texts(segs)).toEqual(['first', 'second']);
  });

  it('does not strip the leading newline when not the first child or not <pre>', () => {
    const segs = splitPreformattedText('\nfirst', 'pre-wrap', {
      isFirstChild: true,
      isPre: false,
      isLastChild: true,
    });
    expect(texts(segs)).toEqual(['', 'first']);
  });

  it('drops a single trailing newline terminator on the last text node', () => {
    expect(texts(splitPreformattedText('a\n', 'pre', { isLastChild: true }))).toEqual(['a']);
  });

  it('keeps a trailing newline when the text node is not the last child', () => {
    // e.g. <pre>line1\n<span>x</span></pre> — the break before the span must survive
    const segs = splitPreformattedText('line1\n', 'pre', { isLastChild: false });
    expect(texts(segs)).toEqual(['line1', '']);
    expect(breaks(segs)).toEqual([true, false]);
  });

  it('normalizes CRLF to a single break', () => {
    expect(texts(splitPreformattedText('a\r\nb', 'pre', { isLastChild: true }))).toEqual(['a', 'b']);
  });

  it('applies text-transform per line', () => {
    expect(texts(splitPreformattedText('aa\nbb', 'pre', { isLastChild: true, textTransform: 'uppercase' }))).toEqual([
      'AA',
      'BB',
    ]);
  });

  it('returns nothing for empty / terminator-only content', () => {
    expect(splitPreformattedText('\n', 'pre', { isLastChild: true })).toEqual([]);
    expect(splitPreformattedText('', 'pre', { isLastChild: true })).toEqual([]);
  });
});
