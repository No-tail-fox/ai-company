/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import portalView from '../src/views/PortalView.vue?raw';
import styles from '../src/styles.css?raw';

test('portal top chrome does not render mac-style window controls', () => {
  expect(portalView).not.toContain('class="window-dots"');
  expect(portalView).not.toContain('class="dot red"');
  expect(portalView).not.toContain('class="dot amber"');
  expect(portalView).not.toContain('class="dot green"');
  expect(styles).not.toContain('grid-template-columns: 110px 170px 1fr;');
});
