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

  it('renders chat box', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
    
    // Vérifie que la chatbox est présente en cherchant un élément plus spécifique
    const chatBoxTitles = screen.getAllByText(/Comment puis-je vous aider \?/i);
    expect(chatBoxTitles.length).toBeGreaterThan(0);
    expect(chatBoxTitles[0]).toBeInTheDocument();
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
