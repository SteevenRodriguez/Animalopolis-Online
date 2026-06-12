import { apiClient } from "./client";
import type { AuditLog, Page } from "@/types/api";

export interface AuditListParams {
  page?: number;
  size?: number;
  desde?: string;
  hasta?: string;
  user_id?: string;
  action?: string;
  resource_type?: string;
  resource_id?: string;
  success?: boolean;
}

export async function listAuditoria(
  params: AuditListParams = {},
): Promise<Page<AuditLog>> {
  const cleaned: Record<string, string | number | boolean> = {};
  for (const [k, v] of Object.entries(params)) {
    if (v !== "" && v !== undefined && v !== null) {
      cleaned[k] = v as string | number | boolean;
    }
  }
  const { data } = await apiClient.get<Page<AuditLog>>("/api/v1/auditoria", {
    params: cleaned,
  });
  return data;
}
