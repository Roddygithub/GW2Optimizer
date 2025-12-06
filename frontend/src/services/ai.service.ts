import { api } from './api';

export interface SkillAnalysisResult {
  skill_id?: number;
  skill_name?: string;
  context?: string;
  rating?: string;
  reason?: string;
  tags?: string[];
  [key: string]: unknown;
}

export interface MetaComparison {
  closest_meta?: {
    id: string;
    name: string;
    profession: string;
    specialization: string;
    role: string;
    stats_text?: string | null;
    runes_text?: string | null;
    source?: string | null;
    notes?: string | null;
  } | null;
  similarity_score?: number;
  recommendations?: string[];
  equipment_comparison?: {
    user_stats?: string | null;
    meta_stats?: string | null;
    stats_match?: boolean;
    user_rune?: string | null;
    meta_rune?: string | null;
    rune_match?: boolean;
    user_sigils?: string[];
    user_relic?: string | null;
  } | null;
  user_role?: string;
  role_confidence?: number;
}

export interface BuildAnalysisResult {
  context?: string;
  synergy_score?: string;
  strengths?: string[];
  weaknesses?: string[];
  summary?: string;
  gear_optimization?: {
    role: string;
    experience: string;
    mode: string;
    chosen: {
      prefix: string;
      rune: string;
      sigils: string[];
      total_damage: number;
      survivability: number;
      overall_score: number;
      reason?: string;
      relic?: string | null;
      rotation_dps_10s?: number | null;
      rotation_total_damage_10s?: number | null;
      rotation_hps_10s?: number | null;
      rotation_total_heal_10s?: number | null;
      example_armor?: Array<{
        slot: string;
        id: number;
        name: string;
        stats?: string | null;
      }>;
    };
    alternatives?: Array<{
      prefix: string;
      rune: string;
      sigils: string[];
      total_damage: number;
      survivability: number;
      overall_score: number;
      relic?: string | null;
    }>;
  };
  meta_comparison?: MetaComparison | null;
  chat_code?: string | null;
  [key: string]: unknown;
}

export interface UrlAnalysisResult {
  source: {
    url: string;
    name?: string | null;
    context?: string | null;
    chat_code?: string | null;
    stats_text?: string | null;
    runes_text?: string | null;
    [key: string]: unknown;
  };
  decoded: {
    specialization_id?: number;
    trait_ids?: number[];
    skill_ids?: number[];
    [key: string]: unknown;
  };
  analysis: BuildAnalysisResult;
  [key: string]: unknown;
}

class AiService {
  async analyzeSkill(skillId: number, context: string = 'WvW Zerg'): Promise<SkillAnalysisResult> {
    const { data } = await api.post<SkillAnalysisResult>('/ai/analyze/skill', {
      skill_id: skillId,
      context,
    });
    return data;
  }

  async analyzeBuild(
    specId: number | null,
    traitIds: number[],
    skillIds: number[],
    context: string = 'WvW Zerg',
  ): Promise<BuildAnalysisResult> {
    const payload: { specialization_id?: number; trait_ids: number[]; skill_ids: number[]; context: string } = {
      trait_ids: traitIds,
      skill_ids: skillIds,
      context,
    };

    if (specId !== null) {
      payload.specialization_id = specId;
    }

    const { data } = await api.post<BuildAnalysisResult>('/ai/analyze/build-full', payload);
    return data;
  }

  async analyzeUrl(url: string, context: string = 'WvW Zerg'): Promise<UrlAnalysisResult> {
    const payload = { url, context };
    const { data } = await api.post<UrlAnalysisResult>('/ai/analyze/url', payload);
    return data;
  }
}

export const aiService = new AiService();
