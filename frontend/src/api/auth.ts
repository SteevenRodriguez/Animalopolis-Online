import { apiClient } from "./client";
import type { LoginResponse, Me } from "@/types/api";

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>("/api/v1/auth/login", {
    email,
    password,
  });
  return data;
}

export async function fetchMe(): Promise<Me> {
  const { data } = await apiClient.get<Me>("/api/v1/auth/me");
  return data;
}
