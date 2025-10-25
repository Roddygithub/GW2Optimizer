import axios from 'axios';
import type { AuthResponse, Build, TeamComposition, User, ChatResponse } from '../types';

const API_BASE_URL = 'http://127.0.0.1:8001/api/v1';

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
    
    const response = await api.post<AuthResponse>('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    
    return response.data;
  },

  register: async (email: string, username: string, password: string): Promise<User> => {
    const response = await api.post<User>('/auth/register', {
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
    const response = await api.get<User>('/auth/me');
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
    const response = await api.get<Build[]>('/builds', { params });
    return response.data;
  },

  get: async (id: string): Promise<Build> => {
    const response = await api.get<Build>(`/builds/${id}`);
    return response.data;
  },

  create: async (build: Partial<Build>): Promise<Build> => {
    const response = await api.post<Build>('/builds', build);
    return response.data;
  },

  update: async (id: string, build: Partial<Build>): Promise<Build> => {
    const response = await api.put<Build>(`/builds/${id}`, build);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/builds/${id}`);
  },

  listPublic: async (params?: {
    skip?: number;
    limit?: number;
    profession?: string;
    game_mode?: string;
    role?: string;
  }): Promise<Build[]> => {
    // For now, use the same endpoint as list since we don't have a separate public endpoint
    const response = await api.get<Build[]>('/builds', { params });
    return response.data;
  },
};

// Chat API
export const chatAPI = {
  sendMessage: async (message: string, version: string): Promise<ChatResponse> => {
    console.log('Envoi du message au chat:', { message, version });
    try {
      const response = await api.post<ChatResponse>('/chat/chat', { 
        message, 
        version 
      });
      
      console.log('Réponse du chat reçue:', response.data);
      
      // S'assurer que la réponse a la structure attendue
      if (!response.data.response) {
        console.warn('La réponse du chat ne contient pas de champ "response"');
        response.data.response = 'Je n\'ai pas pu traiter votre demande.';
      }
      
      // S'assurer que builds_mentioned est un tableau
      if (response.data.builds_mentioned && !Array.isArray(response.data.builds_mentioned)) {
        console.warn('Le champ builds_mentioned n\'est pas un tableau:', response.data.builds_mentioned);
        response.data.builds_mentioned = [];
      }
      
      // S'assurer que suggestions est un tableau
      if (response.data.suggestions && !Array.isArray(response.data.suggestions)) {
        console.warn('Le champ suggestions n\'est pas un tableau:', response.data.suggestions);
        response.data.suggestions = [];
      }
      
      return response.data;
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message au chat:', error);
      return {
        response: 'Une erreur est survenue lors de la communication avec le serveur.',
        builds_mentioned: [],
        suggestions: []
      };
    }
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
