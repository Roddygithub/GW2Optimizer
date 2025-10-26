import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { authAPI, buildsAPI, teamsAPI } from './api';

// Mock axios
const mockAxiosInstance = vi.hoisted(() => ({
  interceptors: {
    request: {
      use: vi.fn(),
      eject: vi.fn()
    },
    response: {
      use: vi.fn(),
      eject: vi.fn()
    }
  },
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  defaults: {
    headers: {
      common: {}
    }
  }
}));

vi.mock('axios', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual as object,
    default: {
      create: vi.fn(() => mockAxiosInstance)
    }
  };
});

// Mock des réponses API
const mockAuthResponse = {
  data: {
    access_token: 'test-token',
    token_type: 'bearer'
  }
};

const mockUser = {
  data: {
    id: '1',
    email: 'test@example.com',
    username: 'testuser',
    is_active: true
  }
};

const mockBuilds = {
  data: [
    {
      id: '1',
      name: 'Test Build',
      profession: 'Guardian',
      game_mode: 'WvW',
      role: 'Support',
      is_public: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    }
  ]
};

const mockTeams = {
  data: [
    {
      id: '1',
      name: 'Test Team',
      game_mode: 'WvW',
      is_public: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    }
  ]
};

// Mock localStorage
const localStorageMock = {
  store: {} as Record<string, string>,
  getItem: vi.fn((key: string) => localStorageMock.store[key] ?? null),
  setItem: vi.fn((key: string, value: string) => {
    localStorageMock.store[key] = value;
  }),
  removeItem: vi.fn((key: string) => {
    delete localStorageMock.store[key];
  }),
  clear: vi.fn(() => {
    localStorageMock.store = {};
  })
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  configurable: true,
  writable: true
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
    beforeEach(() => {
      vi.clearAllMocks();
      mockAxiosInstance.post.mockResolvedValue(mockAuthResponse);
    });

    it('login stores token and returns auth response', async () => {
      const email = 'test@example.com';
      const password = 'password';
      
      const response = await authAPI.login(email, password);
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/auth/token',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
      );
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'test-token');
      expect(response).toEqual(mockAuthResponse.data);
    });

    it('register creates new user', async () => {
      const userData = {
        email: 'test@example.com',
        username: 'testuser',
        password: 'password'
      };
      
      mockAxiosInstance.post.mockResolvedValueOnce(mockUser);
      
      const response = await authAPI.register(
        userData.email,
        userData.username,
        userData.password
      );
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/auth/register',
        userData
      );
      expect(response).toEqual(mockUser.data);
    });

    it('logout removes token from localStorage', () => {
      localStorageMock.setItem('access_token', 'test-token');
      
      authAPI.logout();

      expect(localStorageMock.getItem('access_token')).toBeNull();
    });

    it('getCurrentUser fetches user data', async () => {
      mockAxiosInstance.get.mockResolvedValueOnce(mockUser);
      
      const response = await authAPI.getCurrentUser();
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/auth/me');
      expect(response).toEqual(mockUser.data);
    });
  });

  describe('buildsAPI', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('list fetches builds with params', async () => {
      const params = { profession: 'Guardian', game_mode: 'WvW', limit: 10 };
      mockAxiosInstance.get.mockResolvedValueOnce(mockBuilds);

      const response = await buildsAPI.list(params);
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/builds',
        { params }
      );
      expect(response).toEqual(mockBuilds.data);
    });

    it('get fetches single build', async () => {
      const buildId = '1';
      const mockBuild = {
        data: {
          id: buildId,
          name: 'Test Build',
          profession: 'Guardian',
          game_mode: 'WvW',
          role: 'Support',
          is_public: true,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z'
        }
      };
      
      mockAxiosInstance.get.mockResolvedValueOnce(mockBuild);

      const response = await buildsAPI.get(buildId);
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(`/builds/${buildId}`);
      expect(response).toEqual(mockBuild.data);
    });
  });

  describe('teamsAPI', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('list fetches teams with params', async () => {
      const params = { game_mode: 'WvW', limit: 10 };
      mockAxiosInstance.get.mockResolvedValueOnce(mockTeams);

      const response = await teamsAPI.list(params);
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/teams/',
        { params }
      );
      expect(response).toEqual(mockTeams.data);
    });

    it('get fetches single team', async () => {
      const teamId = '1';
      const mockTeam = {
        data: {
          id: teamId,
          name: 'Test Team',
          game_mode: 'WvW',
          is_public: true,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
          builds: []
        }
      };
      
      mockAxiosInstance.get.mockResolvedValueOnce(mockTeam);

      const response = await teamsAPI.get(teamId);
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(`/api/teams/${teamId}`);
      expect(response).toEqual(mockTeam.data);
    });
  });
});
