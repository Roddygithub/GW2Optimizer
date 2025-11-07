import '@testing-library/jest-dom/vitest';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import BuildsPage from '../Builds';
import * as buildsService from '../../services/builds';

vi.mock('../../services/builds', () => ({
  suggestBuild: vi.fn(),
}));

describe('BuildsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('submits build request and displays result JSON', async () => {
    const suggestBuildMock = vi.mocked(buildsService.suggestBuild);

    suggestBuildMock.mockResolvedValue({
      build: {
        name: 'Celestial Tempest',
        profession: 'Elementalist',
      },
    } as any);

    render(<BuildsPage />);

    fireEvent.click(screen.getByTestId('submit'));

    await waitFor(() => {
      expect(suggestBuildMock).toHaveBeenCalledWith({
        profession: 'Elementalist',
        role: 'DPS',
        game_mode: 'WvW',
      });
    });

    expect(screen.getByTestId('result')).toHaveTextContent('Celestial Tempest');
  });

  it('displays error message when request fails', async () => {
    const suggestBuildMock = vi.mocked(buildsService.suggestBuild);

    suggestBuildMock.mockRejectedValue(new Error('network error'));

    render(<BuildsPage />);

    fireEvent.click(screen.getByTestId('submit'));

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Failed to fetch build suggestion');
    });
  });
});
