export const minPreviewScale = 0.3;
export const maxPreviewScale = 1.2;

export function clampPreviewScale(value: number): number {
  return Math.min(maxPreviewScale, Math.max(minPreviewScale, Number(value.toFixed(2))));
}

export function moveRecord<T extends { id: string }>(records: T[], recordId: string, direction: -1 | 1): T[] | null {
  const index = records.findIndex((record) => record.id === recordId);
  const target = index + direction;
  if (index < 0 || target < 0 || target >= records.length) {
    return null;
  }
  const next = records.slice();
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

export function reorderByDrop<T extends { id: string }>(records: T[], draggedId: string, targetId: string): T[] | null {
  if (!draggedId || draggedId === targetId) {
    return null;
  }
  const draggedIndex = records.findIndex((record) => record.id === draggedId);
  const targetIndex = records.findIndex((record) => record.id === targetId);
  if (draggedIndex < 0 || targetIndex < 0) {
    return null;
  }
  const next = records.slice();
  const [dragged] = next.splice(draggedIndex, 1);
  next.splice(targetIndex, 0, dragged);
  return next;
}
