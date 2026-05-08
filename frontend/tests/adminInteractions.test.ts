import { expect, test } from 'vitest';
import { clampPreviewScale, moveRecord, reorderByDrop } from '../src/services/adminInteractions';

test('clamps preview scale to supported zoom range', () => {
  expect(clampPreviewScale(0.2)).toBe(0.3);
  expect(clampPreviewScale(0.65)).toBe(0.65);
  expect(clampPreviewScale(1.4)).toBe(1.2);
});

test('moves records up and down without mutating the source array', () => {
  const records = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];

  expect(moveRecord(records, 'b', -1)).toEqual([{ id: 'b' }, { id: 'a' }, { id: 'c' }]);
  expect(moveRecord(records, 'b', 1)).toEqual([{ id: 'a' }, { id: 'c' }, { id: 'b' }]);
  expect(records).toEqual([{ id: 'a' }, { id: 'b' }, { id: 'c' }]);
  expect(moveRecord(records, 'a', -1)).toBeNull();
});

test('reorders records by dropping a dragged record onto a target record', () => {
  const records = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];

  expect(reorderByDrop(records, 'c', 'a')).toEqual([{ id: 'c' }, { id: 'a' }, { id: 'b' }]);
  expect(reorderByDrop(records, 'a', 'a')).toBeNull();
  expect(reorderByDrop(records, '', 'a')).toBeNull();
});
