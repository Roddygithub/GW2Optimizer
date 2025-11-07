import { api } from './api';

type Credentials = {
  email: string;
  password: string;
};

type LoginResponse = {
  access_token: string;
  token_type: string;
  user?: {
    id: string;
    email: string;
  };
};

export async function login(email: string, password: string) {
  const { data } = await api.post<LoginResponse>('/auth/login', { email, password });
  return data;
}

export async function register(email: string, password: string) {
  const payload: Credentials = { email, password };
  const { data } = await api.post('/auth/register', payload);
  return data;
}

export async function reset(email: string) {
  const { data } = await api.post('/auth/reset', { email });
  return data;
}

export async function logout() {
  const { data } = await api.post('/auth/logout');
  return data;
}

export async function refresh() {
  const { data } = await api.post('/auth/refresh');
  return data;
}
