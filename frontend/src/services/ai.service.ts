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

export interface BuildAnalysisResult {
  context?: string;
  synergy_score?: string;
  strengths?: string[];
  weaknesses?: string[];
  summary?: string;
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

    const { data } = await api.post<BuildAnalysisResult>('/ai/analyze/build', payload);
    return data;
  }
}

export const aiService = new AiService();
