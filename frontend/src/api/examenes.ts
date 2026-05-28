import { apiClient } from "./client";
import type {
  EstadoEnvio,
  Examen,
  Page,
  PresignedUrl,
  Sede,
  TipoExamen,
} from "@/types/api";

export interface ExamenListParams {
  page?: number;
  size?: number;
  sede?: Sede | "";
  desde?: string;
  hasta?: string;
  estado_envio?: EstadoEnvio | "";
}

export async function listExamenes(
  params: ExamenListParams = {},
): Promise<Page<Examen>> {
  const cleaned: Record<string, string | number> = {};
  for (const [k, v] of Object.entries(params)) {
    if (v !== "" && v !== undefined && v !== null) cleaned[k] = v as string | number;
  }
  const { data } = await apiClient.get<Page<Examen>>("/api/v1/examenes", {
    params: cleaned,
  });
  return data;
}

export async function getExamen(id: string): Promise<Examen> {
  const { data } = await apiClient.get<Examen>(`/api/v1/examenes/${id}`);
  return data;
}

export async function getExamenFileUrl(id: string): Promise<PresignedUrl> {
  const { data } = await apiClient.get<PresignedUrl>(
    `/api/v1/examenes/${id}/file-url`,
  );
  return data;
}

export interface CreateExamenInput {
  sede: Sede;
  nombre_mascota: string;
  nombre_propietario: string;
  whatsapp: string;
  tipo_examen: TipoExamen;
  consentimiento: boolean;
  file: File;
}

export async function createExamen(input: CreateExamenInput): Promise<Examen> {
  const form = new FormData();
  form.append("sede", input.sede);
  form.append("nombre_mascota", input.nombre_mascota);
  form.append("nombre_propietario", input.nombre_propietario);
  form.append("whatsapp", input.whatsapp);
  form.append("tipo_examen", input.tipo_examen);
  form.append("consentimiento", input.consentimiento ? "true" : "false");
  form.append("file", input.file);

  const { data } = await apiClient.post<Examen>("/api/v1/examenes", form);
  return data;
}
