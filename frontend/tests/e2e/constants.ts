export interface RouteMap {
  home: string;
  login: string | null;
  composer: string | null;
  export: string | null;
}

export const ROUTES: RouteMap = {
  home: '/',
  login: null,
  composer: null,
  export: null,
};

export interface LabelMap {
  login: RegExp[];
  composer: RegExp[];
  export: RegExp[];
}

export const LABELS: LabelMap = {
  login: [/login/i, /sign in/i, /connexion/i],
  composer: [/composer/i, /build/i, /optimizer/i],
  export: [/export/i, /share/i],
};
