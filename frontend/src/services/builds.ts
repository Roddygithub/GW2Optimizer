import { api } from './api';

export type SuggestBuildPayload = {
  profession: string;
  role: string;
  game_mode?: string;
};

export type SuggestBuildResponse = {
  build: Record<string, unknown>;
};

export async function suggestBuild(payload: SuggestBuildPayload) {
  const { data } = await api.post<SuggestBuildResponse>('/ai/builds/suggest', payload);
  return data;
}
