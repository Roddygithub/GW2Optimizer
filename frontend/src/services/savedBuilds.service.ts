import { api } from './api';

export interface SavedBuild {
  id: number;
  user_id: string;
  name: string;
  chat_code?: string | null;
  profession?: string | null;
  specialization?: string | null;
  game_mode?: string | null;
  synergy_score?: string | null;
   source_url?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface SavedBuildCreatePayload {
  name: string;
  chat_code?: string | null;
  profession?: string | null;
  specialization?: string | null;
  game_mode?: string | null;
  synergy_score?: string | null;
   source_url?: string | null;
  notes?: string | null;
}

class SavedBuildsService {
  async create(payload: SavedBuildCreatePayload): Promise<SavedBuild> {
    const { data } = await api.post<SavedBuild>('/saved-builds', payload);
    return data;
  }

  async list(): Promise<SavedBuild[]> {
    const { data } = await api.get<SavedBuild[]>('/saved-builds');
    return data;
  }

  async delete(id: number): Promise<void> {
    await api.delete(`/saved-builds/${id}`);
  }
}

export const savedBuildsService = new SavedBuildsService();
