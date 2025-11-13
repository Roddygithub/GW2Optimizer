import '@testing-library/jest-dom/vitest';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ResetPage from '../Reset';
import * as authService from '../../services/auth';

vi.mock('../../services/auth', () => ({
  reset: vi.fn(),
}));

describe('ResetPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('submits reset and shows success message', async () => {
    const resetMock = vi.mocked(authService.reset);
    resetMock.mockResolvedValue({});

    render(<ResetPage />);

    fireEvent.change(screen.getByTestId('email'), { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByTestId('submit'));

    await waitFor(() => {
      expect(resetMock).toHaveBeenCalledWith('user@example.com');
      expect(screen.getByTestId('feedback')).toHaveTextContent('Check your inbox');
    });
  });

  it('surfaces error message on failure', async () => {
    const resetMock = vi.mocked(authService.reset);
    resetMock.mockRejectedValue(new Error('boom'));

    render(<ResetPage />);

    fireEvent.change(screen.getByTestId('email'), { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByTestId('submit'));

    await waitFor(() => {
      expect(screen.getByTestId('feedback')).toHaveTextContent('Reset failed');
    });
  });
});
