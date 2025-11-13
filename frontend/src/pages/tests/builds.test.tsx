import '@testing-library/jest-dom/vitest';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
vi.mock('@/services/builds', () => ({
  suggestBuild: vi.fn(),
  listBuilds: vi.fn(),
  saveBuildSuggestion: vi.fn(),
}));
import * as buildsService from '@/services/builds';
import type { SuggestBuildResponse, BuildSuggestionHistoryItem } from '@/services/builds';
import BuildsPage from '../Builds';

describe('BuildsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('submits build request and displays result JSON', async () => {
    const suggestBuildMock = vi.mocked(buildsService.suggestBuild);
    const listBuildsMock = vi.mocked(buildsService.listBuilds);
    const saveBuildSuggestionMock = vi.mocked(buildsService.saveBuildSuggestion);

    listBuildsMock.mockResolvedValue({ items: [], total: 0, page: 1, limit: 20, has_next: false });

    const suggestResponse: SuggestBuildResponse = {
      build: {
        name: 'Celestial Tempest',
        profession: 'Elementalist',
        role: 'DPS',
      },
      explanation: 'Focus on condition damage.',
    };
    suggestBuildMock.mockResolvedValue(suggestResponse);

    const historyItem: BuildSuggestionHistoryItem = {
      id: 'history-1',
      user_id: null,
      created_at: '2024-05-01T12:00:00Z',
      build: {
        name: 'Celestial Tempest',
        profession: 'Elementalist',
        role: 'DPS',
      },
      explanation: 'Focus on condition damage.',
    };
    saveBuildSuggestionMock.mockResolvedValue(historyItem);

    render(<BuildsPage />);

    await waitFor(() => {
      expect(listBuildsMock).toHaveBeenCalledWith();
    });

    fireEvent.click(screen.getByTestId('submit'));

    await waitFor(() => {
      expect(suggestBuildMock).toHaveBeenCalledWith({
        profession: 'Elementalist',
        role: 'DPS',
        game_mode: 'WvW',
      });
    });

    expect(screen.getByTestId('result')).toHaveTextContent('Celestial Tempest');
    await screen.findByTestId('history-item-history-1');
    await screen.findByText('Elementalist • DPS');
  });

  it('displays error message when request fails', async () => {
    const suggestBuildMock = vi.mocked(buildsService.suggestBuild);
    const listBuildsMock = vi.mocked(buildsService.listBuilds);

    listBuildsMock.mockResolvedValue({ items: [], total: 0, page: 1, limit: 20, has_next: false });
    suggestBuildMock.mockRejectedValue(new Error('network error'));

    render(<BuildsPage />);

    await waitFor(() => {
      expect(listBuildsMock).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByTestId('submit'));

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Failed to fetch build suggestion');
    });
  });

  it('shows history error when loading fails', async () => {
    const listBuildsMock = vi.mocked(buildsService.listBuilds);

    listBuildsMock.mockRejectedValue(new Error('boom'));

    render(<BuildsPage />);

    await screen.findByTestId('history-error');
    expect(screen.getByTestId('history-error')).toHaveTextContent('Failed to load history');
  });
});
