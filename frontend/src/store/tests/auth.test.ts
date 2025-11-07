import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '../auth';

describe('auth store', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null });
  });

  it('sets user information', () => {
    useAuthStore.getState().setUser({ id: '123', email: 'user@example.com' });
    const { user } = useAuthStore.getState();
    expect(user).not.toBeNull();
    expect(user?.email).toBe('user@example.com');
  });

  it('clears user on logout', () => {
    useAuthStore.setState({ user: { id: '123', email: 'user@example.com' } });
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().user).toBeNull();
  });
});
