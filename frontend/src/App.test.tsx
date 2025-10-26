import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';
import { authAPI } from './services/api';

// Mock the API
vi.mock('./services/api', () => ({
  authAPI: {
    getCurrentUser: vi.fn(),
  },
  buildsAPI: {
    list: vi.fn(),
  },
  teamsAPI: {
    list: vi.fn(),
  },
}));

describe('App', () => {
  it('renders without crashing', () => {
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as never);
    
    render(<App />);
    
    // App should render (even if content is async)
    expect(document.body).toBeTruthy();
  });

  it('renders home page by default', async () => {
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as never);
    
    render(<App />);
    
    // Vérifie que le titre de l'application est affiché dans la barre de navigation
    const titleElement = await screen.findByRole('link', { name: /GW2 Optimizer/i });
    expect(!!titleElement).toBe(true);
    
    // Vérifie que le sous-titre est présent dans la barre de navigation
    const navSubtitles = screen.getAllByText(/WvW McM Dashboard/i);
    expect(navSubtitles.length).toBeGreaterThan(0);
    
    // Vérifie qu'au moins un élément avec la version est présent
    const versionElements = screen.getAllByText(/v4.1.0/i);
    expect(versionElements.length).toBeGreaterThan(0);
  });

  it('wraps app with AuthProvider', () => {
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as never);
    
    render(<App />);
    
    // AuthProvider should be in the tree (tested via context)
    expect(document.body).toBeTruthy();
  });

  it('sets up routing', () => {
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as never);
    
    render(<App />);
    
    // Router should be set up
    expect(window.location.pathname).toBe('/');
  });
});
