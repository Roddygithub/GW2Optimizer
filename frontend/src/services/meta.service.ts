import { api } from './api';

export interface MetaProfession {
  profession: string;
  count: number;
  ratio: number;
}

export interface MetaArchetype {
  profession: string | null;
  specialization: string | null;
  synergy_score: string | null;
  occurrences: number;
  frequency: number;
}

export interface MetaSynergy extends MetaArchetype {}

export interface MetaOverviewResponse {
  success: boolean;
  game_mode: string;
  professions: MetaProfession[];
  archetypes: MetaArchetype[];
  synergies: MetaSynergy[];
  raw_meta: unknown;
  timestamp?: string;
}

interface GetMetaOverviewOptions {
  timeRange?: number;
  profession?: string | null;
}

class MetaService {
  async getMetaOverview(
    gameMode: string,
    options: GetMetaOverviewOptions = {},
  ): Promise<MetaOverviewResponse> {
    const params: Record<string, string | number> = {};

    if (options.timeRange != null) {
      params.time_range = options.timeRange;
    }
    if (options.profession) {
      params.profession = options.profession;
    }

    const { data } = await api.get<MetaOverviewResponse>(
      `/meta/overview/${encodeURIComponent(gameMode)}`,
      { params },
    );

    return data;
  }
}

export const metaService = new MetaService();

