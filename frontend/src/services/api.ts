import axios from 'axios';
import type { AuthResponse, Build, TeamComposition, User } from '../types';

const API_BASE_URL = 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await api.post<AuthResponse>('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    
    return response.data;
  },

  register: async (email: string, username: string, password: string): Promise<User> => {
    const response = await api.post<User>('/api/auth/register', {
      email,
      username,
      password,
    });
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/api/auth/me');
    return response.data;
  },
};

// Builds API
export const buildsAPI = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    profession?: string;
    game_mode?: string;
    role?: string;
    is_public?: boolean;
  }): Promise<Build[]> => {
    const response = await api.get<Build[]>('/api/builds/', { params });
    return response.data;
  },

  get: async (id: string): Promise<Build> => {
    const response = await api.get<Build>(`/api/builds/${id}`);
    return response.data;
  },

  create: async (build: Partial<Build>): Promise<Build> => {
    const response = await api.post<Build>('/api/builds/', build);
    return response.data;
  },

  update: async (id: string, build: Partial<Build>): Promise<Build> => {
    const response = await api.put<Build>(`/api/builds/${id}`, build);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/builds/${id}`);
  },

  listPublic: async (params?: {
    skip?: number;
    limit?: number;
    profession?: string;
    game_mode?: string;
    role?: string;
  }): Promise<Build[]> => {
    const response = await api.get<Build[]>('/api/builds/public', { params });
    return response.data;
  },
};

// Teams API
export const teamsAPI = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    game_mode?: string;
    is_public?: boolean;
  }): Promise<TeamComposition[]> => {
    const response = await api.get<TeamComposition[]>('/api/teams/', { params });
    return response.data;
  },

  get: async (id: string): Promise<TeamComposition> => {
    const response = await api.get<TeamComposition>(`/api/teams/${id}`);
    return response.data;
  },

  create: async (team: Partial<TeamComposition>): Promise<TeamComposition> => {
    const response = await api.post<TeamComposition>('/api/teams/', team);
    return response.data;
  },

  update: async (id: string, team: Partial<TeamComposition>): Promise<TeamComposition> => {
    const response = await api.put<TeamComposition>(`/api/teams/${id}`, team);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/teams/${id}`);
  },

  addBuild: async (teamId: string, buildId: string, slotNumber?: number, playerName?: string): Promise<TeamComposition> => {
    const response = await api.post<TeamComposition>(`/api/teams/${teamId}/builds`, {
      build_id: buildId,
      slot_number: slotNumber,
      player_name: playerName,
    });
    return response.data;
  },

  removeBuild: async (teamId: string, slotId: string): Promise<TeamComposition> => {
    const response = await api.delete<TeamComposition>(`/api/teams/${teamId}/builds/${slotId}`);
    return response.data;
  },

  listPublic: async (params?: {
    skip?: number;
    limit?: number;
    game_mode?: string;
  }): Promise<TeamComposition[]> => {
    const response = await api.get<TeamComposition[]>('/api/teams/public', { params });
    return response.data;
  },
};
