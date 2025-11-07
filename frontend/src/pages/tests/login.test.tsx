import '@testing-library/jest-dom/vitest';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from '../Login';
import { useAuthStore } from '../../store/auth';
import * as authService from '../../services/auth';
import * as navigation from '../../lib/navigation';

vi.mock('../../services/auth', () => ({
  login: vi.fn(),
}));

vi.mock('../../lib/navigation', () => ({
  navigate: vi.fn(),
}));

describe('LoginPage', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null });
    vi.clearAllMocks();
  });

  it('submits login, updates store, and navigates to /builds', async () => {
    const loginMock = vi.mocked(authService.login);
    const navigateMock = vi.mocked(navigation.navigate);

    loginMock.mockResolvedValue({
      access_token: 'token',
      token_type: 'bearer',
      user: { id: '1', email: 'user@example.com' },
    } as any);

    render(<LoginPage />);

    fireEvent.change(screen.getByTestId('email'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByTestId('password'), { target: { value: 'password' } });
    fireEvent.click(screen.getByTestId('submit'));

    await waitFor(() => {
      expect(useAuthStore.getState().user?.email).toBe('user@example.com');
    });

    expect(loginMock).toHaveBeenCalledWith('user@example.com', 'password');
    expect(navigateMock).toHaveBeenCalledWith('/builds');
  });
});
