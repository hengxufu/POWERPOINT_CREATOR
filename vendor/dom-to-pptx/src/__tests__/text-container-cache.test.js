import { describe, it, expect } from 'vitest';
import { isTextContainer, isTextContainerCached } from '../utils.js';

describe('isTextContainerCached', () => {
  it('falls back to isTextContainer when cache is null or undefined', () => {
    const p = document.createElement('p');
    p.textContent = 'Sample text';
    expect(isTextContainerCached(p, null)).toBe(isTextContainer(p));
    expect(isTextContainerCached(p, undefined)).toBe(isTextContainer(p));
  });

  it('memoizes classification result in the provided WeakMap cache', () => {
    const p = document.createElement('p');
    p.textContent = 'Cached paragraph';
    const cache = new WeakMap();

    expect(cache.has(p)).toBe(false);
    const result1 = isTextContainerCached(p, cache);
    expect(cache.has(p)).toBe(true);
    expect(cache.get(p)).toBe(result1);

    // Mock cache to verify hit returns cached value
    cache.set(p, 'mocked-result');
    const result2 = isTextContainerCached(p, cache);
    expect(result2).toBe('mocked-result');
  });

  it('keeps distinct caches isolated across export invocations', () => {
    const div = document.createElement('div');
    div.textContent = 'Multi-export text';

    const cacheA = new WeakMap();
    const cacheB = new WeakMap();

    isTextContainerCached(div, cacheA);
    expect(cacheA.has(div)).toBe(true);
    expect(cacheB.has(div)).toBe(false);

    isTextContainerCached(div, cacheB);
    expect(cacheB.has(div)).toBe(true);
  });

  it('accurately distinguishes text containers and non-text containers', () => {
    const cache = new WeakMap();

    const textNode = document.createElement('div');
    textNode.innerHTML = '<span>Inline text</span>';
    expect(isTextContainerCached(textNode, cache)).toBe(true);

    const emptyNode = document.createElement('div');
    expect(isTextContainerCached(emptyNode, cache)).toBe(false);
  });
});
