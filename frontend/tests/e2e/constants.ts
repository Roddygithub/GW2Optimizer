export interface RouteMap {
  home: string;
  login: string | null;
  composer: string | null;
  export: string | null;
}

export const ROUTES: RouteMap = {
  home: '/',
  login: '/login',
  composer: '/ai-build-lab',
  export: '/my-builds',
};

// Base URL for API requests in E2E tests
export const API_BASE_URL = process.env.E2E_API_URL || 'http://gw2optimizer-backend:8000/api/v1';

export interface LabelMap {
  login: RegExp[];
  composer: RegExp[];
  export: RegExp[];
}

export const LABELS: LabelMap = {
  login: [/login/i, /sign in/i, /connexion/i, /se connecter/i],
  composer: [/composer/i, /build/i, /optimizer/i],
  export: [/export/i, /share/i],
};
