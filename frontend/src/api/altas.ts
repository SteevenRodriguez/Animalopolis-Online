import { apiClient } from "./client";
import type {
  Alta,
  EstadoEnvio,
  Page,
  Sede,
  TipoConsulta,
} from "@/types/api";

export interface AltaListParams {
  page?: number;
  size?: number;
  sede?: Sede | "";
  desde?: string;
  hasta?: string;
  estado_envio?: EstadoEnvio | "";
}

export async function listAltas(params: AltaListParams = {}): Promise<Page<Alta>> {
  const cleaned: Record<string, string | number> = {};
  for (const [k, v] of Object.entries(params)) {
    if (v !== "" && v !== undefined && v !== null) cleaned[k] = v as string | number;
  }
  const { data } = await apiClient.get<Page<Alta>>("/api/v1/altas", { params: cleaned });
  return data;
}

export async function getAlta(id: string): Promise<Alta> {
  const { data } = await apiClient.get<Alta>(`/api/v1/altas/${id}`);
  return data;
}

export interface CreateAltaInput {
  sede: Sede;
  nombre_mascota: string;
  nombre_propietario: string;
  whatsapp: string;
  fecha_atencion: string;
  tipo_consulta: TipoConsulta;
  consentimiento: boolean;
}

export async function createAlta(input: CreateAltaInput): Promise<Alta> {
  const { data } = await apiClient.post<Alta>("/api/v1/altas", input);
  return data;
}

export interface UpdateAltaInput {
  fecha_atencion?: string;
  tipo_consulta?: TipoConsulta;
}

export async function updateAlta(id: string, input: UpdateAltaInput): Promise<Alta> {
  const { data } = await apiClient.patch<Alta>(`/api/v1/altas/${id}`, input);
  return data;
}
