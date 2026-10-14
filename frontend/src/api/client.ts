import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import type {
  Voice,
  VoiceListResponse,
  VoiceCreate,
  VoiceUpdate,
  SynthesisJob,
  SynthesisJobListResponse,
  SynthesisJobCreate,
  User,
  TokenResponse,
  LoginRequest,
  HealthResponse,
} from "../types/api";

// Vite provides import.meta.env
declare const importMeta: {
  env: {
    VITE_API_BASE_URL?: string;
  };
};

const API_BASE_URL = importMeta.env.VITE_API_BASE_URL || "/api";

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 30000,
    });

    this.client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      if (this.accessToken && config.headers) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry && this.refreshToken) {
          originalRequest._retry = true;
          try {
            await this.refreshAccessToken();
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${this.accessToken}`;
            }
            return this.client(originalRequest);
          } catch {
            this.clearTokens();
            window.location.href = "/login";
          }
        }
        return Promise.reject(error);
      }
    );

    // Load tokens from sessionStorage
    this.accessToken = sessionStorage.getItem("access_token");
    this.refreshToken = sessionStorage.getItem("refresh_token");
  }

  setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    sessionStorage.setItem("access_token", accessToken);
    sessionStorage.setItem("refresh_token", refreshToken);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>("/health");
    return response.data;
  }

  // Auth
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>("/auth/login", credentials);
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }

  async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) throw new Error("No refresh token");
    const response = await this.client.post<TokenResponse>("/auth/refresh", {
      refresh_token: this.refreshToken,
    });
    this.setTokens(response.data.access_token, response.data.refresh_token);
  }

  async getMe(): Promise<User> {
    const response = await this.client.get<User>("/auth/me");
    return response.data;
  }

  async logout(): Promise<void> {
    this.clearTokens();
  }

  // Voices
  async listVoices(params?: {
    page?: number;
    page_size?: number;
    voice_type?: string;
    language?: string;
    is_active?: boolean;
    search?: string;
  }): Promise<VoiceListResponse> {
    const response = await this.client.get<VoiceListResponse>("/voices", { params });
    return response.data;
  }

  async getVoice(id: number): Promise<Voice> {
    const response = await this.client.get<Voice>(`/voices/${id}`);
    return response.data;
  }

  async createVoice(data: VoiceCreate): Promise<Voice> {
    const response = await this.client.post<Voice>("/voices", data);
    return response.data;
  }

  async updateVoice(id: number, data: VoiceUpdate): Promise<Voice> {
    const response = await this.client.patch<Voice>(`/voices/${id}`, data);
    return response.data;
  }

  async deleteVoice(id: number): Promise<void> {
    await this.client.delete(`/voices/${id}`);
  }

  // Synthesis
  async createSynthesis(data: SynthesisJobCreate): Promise<SynthesisJob> {
    const response = await this.client.post<SynthesisJob>("/synthesis", data);
    return response.data;
  }

  async listSynthesisJobs(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    voice_id?: number;
  }): Promise<SynthesisJobListResponse> {
    const response = await this.client.get<SynthesisJobListResponse>("/synthesis", { params });
    return response.data;
  }

  async getSynthesisJob(id: number): Promise<SynthesisJob> {
    const response = await this.client.get<SynthesisJob>(`/synthesis/${id}`);
    return response.data;
  }

  async downloadSynthesisAudio(jobId: number): Promise<Blob> {
    const response = await this.client.get(`/synthesis/${jobId}/audio`, {
      responseType: "blob",
    });
    return response.data;
  }

  async deleteSynthesisJob(id: number): Promise<void> {
    await this.client.delete(`/synthesis/${id}`);
  }
}

export const api = new ApiClient();