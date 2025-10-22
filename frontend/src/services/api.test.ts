import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import { authAPI, buildsAPI, teamsAPI } from './api';

// Mock axios
vi.mock('axios');

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

describe('API Services', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  afterEach(() => {
    localStorageMock.clear();
  });

  describe('authAPI', () => {
    it('login stores token and returns auth response', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token',
          user: { id: '1', email: 'test@example.com', username: 'testuser' },
        },
      };

      const mockAxios = vi.mocked(axios);
      mockAxios.create = vi.fn().mockReturnValue({
        post: vi.fn().mockResolvedValue(mockResponse),
        get: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any);

      // Re-import to get mocked instance
      const { authAPI: mockedAuthAPI } = await import('./api');
      
      const result = await mockedAuthAPI.login('test@example.com', 'password');

      expect(result.access_token).toBe('test-token');
      expect(localStorageMock.getItem('access_token')).toBe('test-token');
    });

    it('register creates new user', async () => {
      const mockUser = {
        id: '1',
        email: 'new@example.com',
        username: 'newuser',
      };

      const mockAxios = vi.mocked(axios);
      mockAxios.create = vi.fn().mockReturnValue({
        post: vi.fn().mockResolvedValue({ data: mockUser }),
        get: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any);

      const { authAPI: mockedAuthAPI } = await import('./api');
      
      const result = await mockedAuthAPI.register('new@example.com', 'newuser', 'password');

      expect(result).toEqual(mockUser);
    });

    it('logout removes token from localStorage', () => {
      localStorageMock.setItem('access_token', 'test-token');
      
      authAPI.logout();

      expect(localStorageMock.getItem('access_token')).toBeNull();
    });

    it('getCurrentUser fetches user data', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
      };

      const mockAxios = vi.mocked(axios);
      mockAxios.create = vi.fn().mockReturnValue({
        get: vi.fn().mockResolvedValue({ data: mockUser }),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any);

      const { authAPI: mockedAuthAPI } = await import('./api');
      
      const result = await mockedAuthAPI.getCurrentUser();

      expect(result).toEqual(mockUser);
    });
  });

  describe('buildsAPI', () => {
    it('list fetches builds with params', async () => {
      const mockBuilds = [
        { id: '1', name: 'Build 1', profession: 'Guardian' },
        { id: '2', name: 'Build 2', profession: 'Warrior' },
      ];

      const mockAxios = vi.mocked(axios);
      mockAxios.create = vi.fn().mockReturnValue({
        get: vi.fn().mockResolvedValue({ data: mockBuilds }),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any);

      const { buildsAPI: mockedBuildsAPI } = await import('./api');
      
      const result = await mockedBuildsAPI.list({ limit: 10 });

      expect(result).toEqual(mockBuilds);
    });

    it('get fetches single build', async () => {
      const mockBuild = {
        id: '1',
        name: 'Test Build',
        profession: 'Guardian',
      };

      const mockAxios = vi.mocked(axios);
      mockAxios.create = vi.fn().mockReturnValue({
        get: vi.fn().mockResolvedValue({ data: mockBuild }),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any);

      const { buildsAPI: mockedBuildsAPI } = await import('./api');
      
      const result = await mockedBuildsAPI.get('1');

      expect(result).toEqual(mockBuild);
    });
  });

  describe('teamsAPI', () => {
    it('list fetches teams with params', async () => {
      const mockTeams = [
        { id: '1', name: 'Team 1', game_mode: 'zerg' },
        { id: '2', name: 'Team 2', game_mode: 'raid' },
      ];

      const mockAxios = vi.mocked(axios);
      mockAxios.create = vi.fn().mockReturnValue({
        get: vi.fn().mockResolvedValue({ data: mockTeams }),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any);

      const { teamsAPI: mockedTeamsAPI } = await import('./api');
      
      const result = await mockedTeamsAPI.list({ limit: 5 });

      expect(result).toEqual(mockTeams);
    });

    it('get fetches single team', async () => {
      const mockTeam = {
        id: '1',
        name: 'Test Team',
        game_mode: 'zerg',
      };

      const mockAxios = vi.mocked(axios);
      mockAxios.create = vi.fn().mockReturnValue({
        get: vi.fn().mockResolvedValue({ data: mockTeam }),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any);

      const { teamsAPI: mockedTeamsAPI } = await import('./api');
      
      const result = await mockedTeamsAPI.get('1');

      expect(result).toEqual(mockTeam);
    });
  });
});
