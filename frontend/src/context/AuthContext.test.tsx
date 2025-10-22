import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import { authAPI } from '../services/api';
import type { ReactNode } from 'react';

// Mock the API
vi.mock('../services/api', () => ({
  authAPI: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  afterEach(() => {
    localStorageMock.clear();
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  it('throws error when useAuth is used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleErrorSpy.mockRestore();
  });

  it('provides initial auth state', async () => {
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as any);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('initializes with stored token', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      username: 'testuser',
    };

    localStorageMock.setItem('access_token', 'test-token');
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(mockUser as any);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('handles login successfully', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      username: 'testuser',
    };

    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as any);
    vi.mocked(authAPI.login).mockResolvedValue({
      user: mockUser,
      access_token: 'new-token',
    } as any);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('handles register successfully', async () => {
    const mockUser = {
      id: '1',
      email: 'new@example.com',
      username: 'newuser',
    };

    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(null as any);
    vi.mocked(authAPI.register).mockResolvedValue(mockUser as any);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.register('new@example.com', 'newuser', 'password');
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('handles logout', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      username: 'testuser',
    };

    localStorageMock.setItem('access_token', 'test-token');
    vi.mocked(authAPI.getCurrentUser).mockResolvedValue(mockUser as any);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorageMock.getItem('access_token')).toBeNull();
  });

  it('removes token on failed getCurrentUser', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    localStorageMock.setItem('access_token', 'invalid-token');
    vi.mocked(authAPI.getCurrentUser).mockRejectedValue(new Error('Unauthorized'));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(localStorageMock.getItem('access_token')).toBeNull();

    consoleErrorSpy.mockRestore();
  });
});
