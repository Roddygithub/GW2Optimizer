import '@testing-library/jest-dom/vitest';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RegisterPage from '../Register';
import * as authService from '../../services/auth';
import * as navigation from '../../lib/navigation';

vi.mock('../../services/auth', () => ({
  register: vi.fn(),
}));

vi.mock('../../lib/navigation', () => ({
  navigate: vi.fn(),
}));

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('submits register, shows success message, and navigates to /login', async () => {
    const registerMock = vi.mocked(authService.register);
    const navigateMock = vi.mocked(navigation.navigate);

    registerMock.mockResolvedValue({});

    render(<RegisterPage />);

    fireEvent.change(screen.getByTestId('email'), { target: { value: 'new@example.com' } });
    fireEvent.change(screen.getByTestId('password'), { target: { value: 'secret' } });
    fireEvent.click(screen.getByTestId('submit'));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith('new@example.com', 'secret');
    });

    const feedback = await screen.findByTestId('feedback');
    expect(feedback).toHaveTextContent('Registered. Please login.');

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/login');
    });
  });

  it('surfaces error message on failure', async () => {
    const registerMock = vi.mocked(authService.register);

    registerMock.mockRejectedValue(new Error('boom'));

    render(<RegisterPage />);

    fireEvent.change(screen.getByTestId('email'), { target: { value: 'new@example.com' } });
    fireEvent.change(screen.getByTestId('password'), { target: { value: 'secret' } });
    fireEvent.click(screen.getByTestId('submit'));

    const feedback = await screen.findByTestId('feedback');
    expect(feedback).toHaveTextContent('Registration failed');

    expect(registerMock).toHaveBeenCalledWith('new@example.com', 'secret');
  });
});
