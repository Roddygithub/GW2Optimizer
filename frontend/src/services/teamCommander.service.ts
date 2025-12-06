import { api } from './api';

interface TeamCommandResponse {
  success: boolean;
  team_size: number;
  groups: Array<{
    index: number;
    slots: Array<{
      role: string;
      profession: string;
      specialization: string;
      equipment: {
        stats: string;
        rune: string;
        sigils: string[];
        relic?: string | null;
        example_armor?: Array<{
          slot: string;
          id: number;
          name: string;
          stats?: string | null;
        }>;
      };
      performance: {
        burst_damage: number;
        survivability: number;
        dps_increase: number;
      };
      advisor_reason?: string;
    }>;
  }>;
  synergy: {
    score: string;
    details: {
      stability?: string;
      healing?: string;
      boon_share?: string;
      boon_strip?: string;
      damage?: string;
      cleanse?: string;
    };
  };
  notes: string[];
}

interface TeamTemplate {
  name: string;
  description: string;
  command: string;
}

export const teamCommanderApi = {
  /**
   * Send a natural language command to build a WvW team
   */
  async command(
    message: string,
    experience?: 'beginner' | 'intermediate' | 'expert',
    mode?: 'wvw_zerg' | 'wvw_outnumber' | 'wvw_roam'
  ): Promise<TeamCommandResponse> {
    const payload: { message: string; experience?: string; mode?: string } = { message };

    if (experience) {
      payload.experience = experience;
    }

    if (mode) {
      payload.mode = mode;
    }

    const response = await api.post<TeamCommandResponse>('/ai/teams/command', payload);
    return response.data;
  },

  /**
   * Get predefined team templates
   */
  async getTemplates(): Promise<{ templates: TeamTemplate[] }> {
    const response = await api.get<{ templates: TeamTemplate[] }>('/ai/teams/templates');
    return response.data;
  },
};
