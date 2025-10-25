/**
 * AI Service Client v4.1.0
 * 
 * Client TypeScript pour communiquer avec AI Core backend.
 * Gère toutes les requêtes vers /api/ai/*
 * 
 * Endpoints:
 *   - POST /api/ai/compose - Générer composition
 *   - POST /api/ai/feedback - Soumettre feedback
 *   - GET /api/ai/context - Récupérer méta actuelle
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Build {
  profession: string;
  specialization?: string;
  role: string;
  count: number;
  priority: string;
  description: string;
  key_boons: string[];
}

export interface TeamComposition {
  id: string;
  name: string;
  size: number;
  game_mode: string;
  builds: Build[];
  strategy: string;
  strengths: string[];
  weaknesses: string[];
  synergy_score: number;
  metadata: {
    source: string;
    model?: string;
    request_id: string;
    preferences?: Record<string, any>;
  };
  timestamp: string;
  user_id?: string;
  request_id?: string;
}

export interface ComposeRequest {
  game_mode: string;
  team_size?: number | null;
  preferences?: Record<string, any>;
}

export interface FeedbackRequest {
  composition_id: string;
  rating: number;
  comments?: string;
}

export interface MetaContext {
  current_meta: {
    last_update: string;
    source: string;
    trending_professions: string[];
  };
  trending_builds: any[];
  recent_changes: any[];
  note?: string;
}

export class AIServiceError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'AIServiceError';
  }
}

/**
 * Client pour AI Core API
 */
class AIService {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Configure le token d'authentification
   */
  setToken(token: string) {
    this.token = token;
  }

  /**
   * Récupère le token depuis localStorage
   */
  private getToken(): string | null {
    if (this.token) return this.token;
    
    // Try to get from localStorage
    const stored = localStorage.getItem('access_token');
    if (stored) {
      this.token = stored;
      return stored;
    }
    
    return null;
  }

  /**
   * Effectue une requête HTTP
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new AIServiceError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof AIServiceError) {
        throw error;
      }

      // Network error
      throw new AIServiceError(
        'Erreur réseau: Impossible de contacter le serveur AI',
        0,
        error
      );
    }
  }

  /**
   * Génère une composition d'équipe
   * 
   * @param request - Paramètres de composition
   * @returns Composition générée par l'IA
   * 
   * @example
   * ```ts
   * const composition = await aiService.composeTeam({
   *   game_mode: 'zerg',
   *   team_size: null, // Auto-adapté
   *   preferences: { focus: 'boons' }
   * });
   * ```
   */
  async composeTeam(request: ComposeRequest): Promise<TeamComposition> {
    return this.request<TeamComposition>('/api/ai/compose', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Soumet un feedback sur une composition
   * 
   * @param feedback - Feedback utilisateur
   * @returns Confirmation
   * 
   * @example
   * ```ts
   * await aiService.submitFeedback({
   *   composition_id: 'uuid-123',
   *   rating: 8,
   *   comments: 'Excellente composition!'
   * });
   * ```
   */
  async submitFeedback(feedback: FeedbackRequest): Promise<{
    status: string;
    message: string;
    composition_id: string;
  }> {
    return this.request('/api/ai/feedback', {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  }

  /**
   * Récupère le contexte méta actuel
   * 
   * @returns Méta GW2 actuelle
   * 
   * @example
   * ```ts
   * const meta = await aiService.getContext();
   * console.log(meta.current_meta.trending_professions);
   * ```
   */
  async getContext(): Promise<MetaContext> {
    return this.request<MetaContext>('/api/ai/context', {
      method: 'GET',
    });
  }
}

// Export singleton instance
export const aiService = new AIService();

// Export class for testing
export { AIService };
