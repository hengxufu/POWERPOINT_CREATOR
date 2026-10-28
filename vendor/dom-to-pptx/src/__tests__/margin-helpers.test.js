import { describe, it, expect } from 'vitest';
import { createShapeMargin, createTableCellMargin } from '../utils.js';

describe('margin helpers', () => {
  it('createShapeMargin normalizes CSS (top, right, bottom, left) to PptxGenJS [lIns, rIns, bIns, tIns]', () => {
    const top = 10;
    const right = 20;
    const bottom = 30;
    const left = 40;

    const shapeMargin = createShapeMargin(top, right, bottom, left);
    expect(shapeMargin).toEqual([40, 20, 30, 10]); // [left, right, bottom, top]
  });

  it('createTableCellMargin normalizes CSS (top, right, bottom, left) to PptxGenJS [marT, marR, marB, marL]', () => {
    const top = 10;
    const right = 20;
    const bottom = 30;
    const left = 40;

    const cellMargin = createTableCellMargin(top, right, bottom, left);
    expect(cellMargin).toEqual([10, 20, 30, 40]); // [top, right, bottom, left]
  });
});
