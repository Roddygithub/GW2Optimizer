import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Home } from './Home';

describe('Home Page', () => {
  it('renders hero section', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
    
    expect(screen.getByText(/Optimisez vos Escouades WvW/i)).toBeInTheDocument();
  });

  it('renders CTA buttons', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
    
    expect(screen.getByText(/Accéder au Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Explorer les Builds/i)).toBeInTheDocument();
  });

  it('renders feature cards', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
    
    expect(screen.getByText(/Gestion d'Escouades/i)).toBeInTheDocument();
    expect(screen.getByText(/Bibliothèque de Builds/i)).toBeInTheDocument();
    expect(screen.getByText(/Statistiques Avancées/i)).toBeInTheDocument();
  });

  it('renders Ollama branding', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
    
    expect(screen.getByText(/Empowered by Ollama with Mistral/i)).toBeInTheDocument();
  });
});
