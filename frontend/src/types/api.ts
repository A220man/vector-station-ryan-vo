export type VoiceType = "builtin" | "cloned" | "designed";
export type SynthesisStatus = "pending" | "processing" | "completed" | "failed";
export type UserRole = "viewer" | "operator" | "admin";

export interface Voice {
  id: number;
  name: string;
  description: string | null;
  voice_type: VoiceType;
  language: string;
  sample_rate: number;
  model_id: string | null;
  reference_audio_path: string | null;
  design_params: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  owner_id: number | null;
}

export interface VoiceListResponse {
  voices: Voice[];
  total: number;
  page: number;
  page_size: number;
}

export interface VoiceCreate {
  name: string;
  description?: string;
  language?: string;
  sample_rate?: number;
  voice_type: VoiceType;
  model_id?: string;
  reference_audio_path?: string;
  design_params?: string;
}

export interface VoiceUpdate {
  name?: string;
  description?: string;
  language?: string;
  is_active?: boolean;
}

export interface SynthesisJob {
  id: number;
  text: string;
  voice_id: number;
  status: SynthesisStatus;
  output_path: string | null;
  duration_seconds: number | null;
  error_message: string | null;
  speed: number;
  pitch: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  owner_id: number | null;
  voice?: Voice;
}

export interface SynthesisJobListResponse {
  jobs: SynthesisJob[];
  total: number;
  page: number;
  page_size: number;
}

export interface SynthesisJobCreate {
  text: string;
  voice_id: number;
  speed?: number;
  pitch?: number;
}

export interface User {
  id: number;
  email: string;
  username: string | null;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_superuser: boolean;
  oidc_sub: string | null;
  oidc_provider: string | null;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}