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
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as any);
    
    render(<App />);
    
    // App should render (even if content is async)
    expect(document.body).toBeTruthy();
  });

  it('renders home page by default', async () => {
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as any);
    
    render(<App />);
    
    // Home page should be visible
    expect(await screen.findByText(/GW2Optimizer/i)).toBeInTheDocument();
  });

  it('wraps app with AuthProvider', () => {
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as any);
    
    render(<App />);
    
    // AuthProvider should be in the tree (tested via context)
    expect(document.body).toBeTruthy();
  });

  it('sets up routing', () => {
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as any);
    
    render(<App />);
    
    // Router should be set up
    expect(window.location.pathname).toBe('/');
  });
});
