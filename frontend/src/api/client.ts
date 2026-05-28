import axios, { AxiosError } from "axios";
import type { ApiErrorBody } from "@/types/api";

const baseURL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL,
  timeout: 30_000,
});

const TOKEN_KEY = "animalopolis.token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

apiClient.interceptors.response.use(
  (r) => r,
  (error: AxiosError<ApiErrorBody>) => {
    if (error.response?.status === 401 && onUnauthorized) {
      onUnauthorized();
    }
    return Promise.reject(error);
  },
);

export function extractApiError(error: unknown, fallback = "Error inesperado"): string {
  if (axios.isAxiosError(error)) {
    const body = error.response?.data as ApiErrorBody | undefined;
    return body?.error?.message ?? error.message ?? fallback;
  }
  if (error instanceof Error) return error.message;
  return fallback;
}
