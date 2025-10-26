import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { Home } from './Home';

describe('Home Page', () => {
  it('renders hero section', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
    
    // Vérifie que le titre principal est affiché
    expect(screen.getByText(/Assistant IA pour Compositions WvW/i)).toBeInTheDocument();
  });

  it('renders chat box', async () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
    
    // Vérifie que la chatbox est présente en tenant compte des duplications responsive
    const chatBoxTitles = await screen.findAllByText(/Assistant GW2 Optimizer/i);
    expect(chatBoxTitles.length).toBeGreaterThan(0);
  });

  it('renders version info', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
    
    // Vérifie que la version est affichée en cherchant une partie du texte
    const versionElements = screen.getAllByText(/GW2 Optimizer v4.1.0/i);
    expect(versionElements.length).toBeGreaterThan(0);
    expect(versionElements[0]).toBeInTheDocument();
  });
});
