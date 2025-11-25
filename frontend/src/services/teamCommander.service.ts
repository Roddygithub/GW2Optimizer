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
      };
      performance: {
        burst_damage: number;
        survivability: number;
        dps_increase: number;
      };
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
  async command(message: string): Promise<TeamCommandResponse> {
    const response = await api.post<TeamCommandResponse>('/ai/teams/command', {
      message,
    });
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
