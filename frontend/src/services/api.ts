import axios, { type InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers = (config.headers || {}) as any;
    // Axios typings autorisent l'accès direct au header Authorization
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});
