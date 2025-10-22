// API Types matching backend models

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Build {
  id: string;
  user_id: string;
  name: string;
  profession: Profession;
  specialization?: string;
  game_mode: GameMode;
  role: Role;
  description?: string;
  trait_lines: TraitLine[];
  skills: Skill[];
  equipment: Equipment[];
  synergies: string[];
  counters: string[];
  tags: string[];
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface TeamComposition {
  id: string;
  user_id: string;
  name: string;
  game_mode: GameMode;
  team_size: number;
  description?: string;
  synergies: string[];
  weaknesses: string[];
  strengths: string[];
  overall_rating?: number;
  is_public: boolean;
  slots: TeamSlot[];
  created_at: string;
  updated_at: string;
}

export interface TeamSlot {
  id: string;
  team_composition_id: string;
  build_id: string;
  slot_number: number;
  player_name?: string;
  priority: number;
  build?: Build;
}

export interface TraitLine {
  id: number;
  name: string;
  traits: number[];
}

export interface Skill {
  slot: string;
  id: number;
  name: string;
}

export interface Equipment {
  slot: string;
  id: number;
  name: string;
  stats?: string;
  rune?: string;
  sigil?: string;
}

export type Profession = 
  | "Guardian"
  | "Warrior"
  | "Engineer"
  | "Ranger"
  | "Thief"
  | "Elementalist"
  | "Mesmer"
  | "Necromancer"
  | "Revenant";

export type GameMode = 
  | "pve"
  | "pvp"
  | "wvw"
  | "raid"
  | "fractal"
  | "strike"
  | "zerg"
  | "roaming";

export type Role = 
  | "dps"
  | "support"
  | "healer"
  | "tank"
  | "boon"
  | "condi"
  | "power"
  | "hybrid";

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApiError {
  detail: string;
}
