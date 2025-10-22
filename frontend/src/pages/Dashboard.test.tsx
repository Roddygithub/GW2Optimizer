import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from './Dashboard';
import { teamsAPI, buildsAPI } from '../services/api';

// Mock the API modules
vi.mock('../services/api', () => ({
  teamsAPI: {
    list: vi.fn(),
  },
  buildsAPI: {
    list: vi.fn(),
  },
}));

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    // Mock API calls to never resolve
    vi.mocked(teamsAPI.list).mockImplementation(() => new Promise(() => {}));
    vi.mocked(buildsAPI.list).mockImplementation(() => new Promise(() => {}));

    render(<Dashboard />);
    
    // Check for loading spinner
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('renders dashboard header after loading', async () => {
    // Mock successful API responses
    vi.mocked(teamsAPI.list).mockResolvedValue([]);
    vi.mocked(buildsAPI.list).mockResolvedValue([]);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Dashboard McM WvW/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Gestion d'escouades et optimisation/i)).toBeInTheDocument();
  });

  it('displays stats cards', async () => {
    const mockTeams = [
      { id: '1', name: 'Team 1' },
      { id: '2', name: 'Team 2' },
    ];
    const mockBuilds = [
      { id: '1', name: 'Build 1' },
      { id: '2', name: 'Build 2' },
      { id: '3', name: 'Build 3' },
    ];

    vi.mocked(teamsAPI.list).mockResolvedValue(mockTeams as any);
    vi.mocked(buildsAPI.list).mockResolvedValue(mockBuilds as any);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Dashboard McM WvW/i)).toBeInTheDocument();
    });

    // Check for stats cards
    expect(screen.getByText(/Compositions/i)).toBeInTheDocument();
    expect(screen.getByText(/Builds/i)).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    vi.mocked(teamsAPI.list).mockRejectedValue(new Error('API Error'));
    vi.mocked(buildsAPI.list).mockRejectedValue(new Error('API Error'));

    render(<Dashboard />);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to fetch dashboard data:',
        expect.any(Error)
      );
    });

    consoleErrorSpy.mockRestore();
  });

  it('fetches data on mount', async () => {
    vi.mocked(teamsAPI.list).mockResolvedValue([]);
    vi.mocked(buildsAPI.list).mockResolvedValue([]);

    render(<Dashboard />);

    await waitFor(() => {
      expect(teamsAPI.list).toHaveBeenCalledWith({ limit: 5 });
      expect(buildsAPI.list).toHaveBeenCalledWith({ limit: 10 });
    });
  });

  it('displays recent teams section', async () => {
    const mockTeams = [
      { id: '1', name: 'Zerg Team Alpha', game_mode: 'zerg' },
    ];

    vi.mocked(teamsAPI.list).mockResolvedValue(mockTeams as any);
    vi.mocked(buildsAPI.list).mockResolvedValue([]);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Compositions Récentes/i)).toBeInTheDocument();
    });
  });

  it('displays recent builds section', async () => {
    const mockBuilds = [
      { id: '1', name: 'Guardian Support', profession: 'Guardian' },
    ];

    vi.mocked(teamsAPI.list).mockResolvedValue([]);
    vi.mocked(buildsAPI.list).mockResolvedValue(mockBuilds as any);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Builds Récents/i)).toBeInTheDocument();
    });
  });
});
