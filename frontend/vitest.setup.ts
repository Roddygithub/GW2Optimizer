// Import des extensions de Jest DOM pour les tests
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Nettoyage après chaque test
afterEach(() => {
  cleanup();
});
