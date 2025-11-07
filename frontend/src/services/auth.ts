import { api } from "./api";

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

export async function logout() {
  const { data } = await api.post("/auth/logout");
  return data;
}

export async function refresh() {
  const { data } = await api.post("/auth/refresh");
  return data;
}
