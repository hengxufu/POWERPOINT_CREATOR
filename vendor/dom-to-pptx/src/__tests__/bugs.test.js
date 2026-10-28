import { describe, it, expect, beforeAll, vi } from 'vitest';
import { collectTextParts } from '../utils.js';
import { exportToPptx } from '../index.js';

// Mock pptxgenjs
const mockAddText = vi.fn();
const mockAddSlide = vi.fn(() => ({
  addText: mockAddText,
  addShape: vi.fn(),
  addImage: vi.fn(),
  addTable: vi.fn(),
}));

vi.mock('pptxgenjs', () => {
  const mockShapeType = { rect: 'rect', roundRect: 'roundRect', ellipse: 'ellipse' };
  return {
    default: vi.fn().mockImplementation(function () {
      return {
        defineLayout: vi.fn(),
        addSlide: mockAddSlide,
        write: vi.fn(() => Promise.resolve('')),
        ShapeType: mockShapeType,
      };
    }),
  };
});

describe('Bug 2: Inline styled badges keep highlight', () => {
  beforeAll(() => {
    // Mock HTMLCanvasElement.prototype.getContext for JSDOM env
    let fillStyle = '';
    HTMLCanvasElement.prototype.getContext = () => ({
      get fillStyle() {
        return fillStyle;
      },
      set fillStyle(val) {
        fillStyle = val;
      },
      clearRect: () => {},
      fillRect: () => {},
      getImageData: () => ({ data: [0, 0, 0, 0] }),
    });
  });

  it('should keep highlight on inline elements and delete on block elements', () => {
    // Test case 1: inline-block element (e.g. badge)
    const span = document.createElement('span');
    span.style.backgroundColor = 'blue';
    span.style.display = 'inline-block';
    const textNode = document.createTextNode('LABEL');
    span.appendChild(textNode);
    document.body.appendChild(span);

    const partsSpan = collectTextParts(span, window.getComputedStyle(span), 1);
    expect(partsSpan[0].options.highlight).toBeDefined();

    // Test case 2: block element (e.g. div)
    const div = document.createElement('div');
    div.style.backgroundColor = 'blue';
    div.style.display = 'block';
    const textNodeDiv = document.createTextNode('LABEL');
    div.appendChild(textNodeDiv);
    document.body.appendChild(div);

    const partsDiv = collectTextParts(div, window.getComputedStyle(div), 1);
    expect(partsDiv[0].options.highlight).toBeUndefined();

    // Clean up
    document.body.removeChild(span);
    document.body.removeChild(div);
  });
});

describe('Bug 3: No duplicate rendering of inline elements', () => {
  it('should not render independent shape+text for span child inside text container', async () => {
    mockAddText.mockClear();

    const container = document.createElement('div');
    container.className = 'slide';
    container.style.width = '960px';
    container.style.height = '540px';

    const div = document.createElement('div');
    div.innerHTML = 'Some text <span>PMA</span> other text';
    container.appendChild(div);
    document.body.appendChild(container);

    // Mock layout measurements
    container.getBoundingClientRect = () => ({ width: 960, height: 540, left: 0, top: 0, right: 960, bottom: 540 });
    div.getBoundingClientRect = () => ({ width: 900, height: 100, left: 30, top: 30, right: 930, bottom: 130 });
    const span = div.querySelector('span');
    span.getBoundingClientRect = () => ({ width: 50, height: 20, left: 150, top: 35, right: 200, bottom: 55 });

    await exportToPptx(container, { skipDownload: true, skipNormalize: true });

    // Assert that we don't have separate text box for 'PMA'
    // The text 'PMA' should only be present inside the main text box containing the full parts list.
    const pmaCalls = mockAddText.mock.calls.filter((call) => {
      const [textParts] = call;
      if (Array.isArray(textParts)) {
        const textStr = textParts.map(p => p.text).join('').trim();
        return textStr === 'PMA';
      }
      return false;
    });

    expect(pmaCalls.length).toBe(0);

    document.body.removeChild(container);
  });
});
