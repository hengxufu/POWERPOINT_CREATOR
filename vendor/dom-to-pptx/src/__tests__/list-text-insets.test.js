import { beforeAll, describe, expect, it } from 'vitest';
import JSZip from 'jszip';
import { exportToPptx } from '../index.js';

// A 1920px-wide root is exported as a 10in slide, so 1 CSS px is 914400 / 96 / 2 EMU,
// and 1 CSS px of padding is 0.75 / 2 pt.
const EMU_PER_PT = 12700;
const PT_PER_PX = 0.75 * 0.5;

function rect({ left, top, width, height }) {
  return {
    x: left,
    y: top,
    left,
    top,
    width,
    height,
    right: left + width,
    bottom: top + height,
    toJSON() {
      return this;
    },
  };
}

beforeAll(() => {
  let fillStyle = '';
  HTMLCanvasElement.prototype.getContext = () => ({
    get fillStyle() {
      return fillStyle;
    },
    set fillStyle(value) {
      fillStyle = value;
    },
    clearRect: () => {},
    fillRect: () => {},
    getImageData: () => ({ data: [0, 0, 0, 255] }),
  });
});

describe('list text insets', () => {
  it('maps each CSS padding edge of a <ul> to the matching PPTX inset', async () => {
    // Four distinct paddings, so a swapped pair cannot go unnoticed.
    const paddingPx = { top: 12, right: 4, bottom: 8, left: 20 };

    const slide = document.createElement('div');
    slide.setAttribute('style', 'position:relative;width:1920px;height:1080px;background:#fff');

    const list = document.createElement('ul');
    list.setAttribute(
      'style',
      'position:absolute;left:200px;top:200px;width:400px;height:120px;color:#111;font-size:16px;' +
        `line-height:25px;margin:0;padding:${paddingPx.top}px ${paddingPx.right}px ${paddingPx.bottom}px ${paddingPx.left}px`
    );
    for (const text of ['First item', 'Second item']) {
      const item = document.createElement('li');
      item.setAttribute('style', 'font-size:16px;line-height:25px');
      item.textContent = text;
      list.appendChild(item);
    }

    slide.appendChild(list);
    document.body.appendChild(slide);

    slide.getBoundingClientRect = () => rect({ left: 0, top: 0, width: 1920, height: 1080 });
    list.getBoundingClientRect = () => rect({ left: 200, top: 200, width: 400, height: 120 });
    Array.from(list.children).forEach((item, index) => {
      item.getBoundingClientRect = () => rect({ left: 220, top: 212 + index * 25, width: 376, height: 25 });
    });

    try {
      const blob = await exportToPptx(slide, { skipDownload: true, autoEmbedFonts: false });
      const zip = await JSZip.loadAsync(blob);
      const xml = await zip.file('ppt/slides/slide1.xml').async('string');

      const doc = new DOMParser().parseFromString(xml, 'text/xml');
      const listShape = Array.from(doc.getElementsByTagName('p:sp')).find((shape) =>
        Array.from(shape.getElementsByTagName('a:t')).some((run) => run.textContent.includes('First item'))
      );
      expect(listShape).toBeDefined();

      const bodyPr = listShape.getElementsByTagName('a:bodyPr')[0];
      const insetEmu = (px) => Math.round(px * PT_PER_PX * EMU_PER_PT);

      expect(Number(bodyPr.getAttribute('lIns'))).toBe(insetEmu(paddingPx.left));
      expect(Number(bodyPr.getAttribute('rIns'))).toBe(insetEmu(paddingPx.right));
      expect(Number(bodyPr.getAttribute('bIns'))).toBe(insetEmu(paddingPx.bottom));
      expect(Number(bodyPr.getAttribute('tIns'))).toBe(insetEmu(paddingPx.top));
    } finally {
      slide.remove();
    }
  });

  it('assigns hierarchical indentLevel to indented sub-bullets instead of bloating hanging indent', async () => {
    const slide = document.createElement('div');
    slide.setAttribute('style', 'position:relative;width:1920px;height:1080px;background:#fff');

    const list = document.createElement('ul');
    list.setAttribute(
      'style',
      'position:absolute;left:200px;top:200px;width:500px;height:150px;color:#111;font-size:16px;line-height:25px;margin:0;padding:10px'
    );

    const liRoot = document.createElement('li');
    liRoot.textContent = 'Root bullet';
    const liSub = document.createElement('li');
    liSub.className = 'sub';
    liSub.textContent = 'Sub bullet indented';
    // Indent sub-bullet by 24px (1 indent level)
    liSub.setAttribute('style', 'margin-left: 24px;');

    list.appendChild(liRoot);
    list.appendChild(liSub);
    slide.appendChild(list);
    document.body.appendChild(slide);

    slide.getBoundingClientRect = () => rect({ left: 0, top: 0, width: 1920, height: 1080 });
    list.getBoundingClientRect = () => rect({ left: 200, top: 200, width: 500, height: 150 });
    // Root li at x=210 (due to ul padding 10)
    liRoot.getBoundingClientRect = () => rect({ left: 210, top: 210, width: 480, height: 25 });
    // Sub li shifted right by 24px -> x=234
    liSub.getBoundingClientRect = () => rect({ left: 234, top: 235, width: 456, height: 25 });

    try {
      const blob = await exportToPptx(slide, { skipDownload: true, autoEmbedFonts: false });
      const zip = await JSZip.loadAsync(blob);
      const xml = await zip.file('ppt/slides/slide1.xml').async('string');

      const doc = new DOMParser().parseFromString(xml, 'text/xml');
      const paragraphs = Array.from(doc.getElementsByTagName('a:p'));

      const subP = paragraphs.find((p) =>
        Array.from(p.getElementsByTagName('a:t')).some((t) => t.textContent.includes('Sub bullet indented'))
      );
      expect(subP).toBeDefined();

      const pPr = subP.getElementsByTagName('a:pPr')[0];
      expect(pPr).toBeDefined();

      // lvl attribute must be 1 for sub-bullet
      expect(pPr.getAttribute('lvl')).toBe('1');

      // indent should be negative standard hanging indent (-10pt scaled = -127000 EMU)
      // and marL should be indentLevel adjusted (marL + marL * lvl)
      const marL = Number(pPr.getAttribute('marL'));
      const indent = Number(pPr.getAttribute('indent'));
      expect(indent).toBeLessThan(0);
      expect(marL).toBeGreaterThan(0);
    } finally {
      slide.remove();
    }
  });
});

