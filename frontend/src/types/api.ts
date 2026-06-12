export type Rol = "admin" | "staff" | "consulta";
export type Sede = "urdesa" | "ciudad_celeste";
export type EstadoEnvio = "pendiente" | "enviado" | "fallido";

export type TipoConsulta =
  | "primera_consulta"
  | "control"
  | "vacunacion"
  | "desparasitacion"
  | "emergencia"
  | "cirugia"
  | "otro";

export type TipoExamen =
  | "sangre"
  | "orina"
  | "heces"
  | "radiografia"
  | "ecografia"
  | "citologia"
  | "otro";

export interface LoginResponse {
  access_token: string;
  token_type: string;
  rol: Rol;
  sede: Sede | null;
  nombre: string;
}

export interface Me {
  id: string;
  email: string;
  nombre: string;
  rol: Rol;
  sede: Sede | null;
  is_active: boolean;
}

export interface Alta {
  id: string;
  sede: Sede;
  mascota_id: string;
  propietario_id: string;
  fecha_atencion: string;
  tipo_consulta: TipoConsulta;
  consentimiento: boolean;
  estado_envio: EstadoEnvio;
  enviado_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Examen {
  id: string;
  sede: Sede;
  mascota_id: string;
  propietario_id: string;
  tipo_examen: TipoExamen;
  archivo_nombre: string;
  archivo_mime: string;
  archivo_size_bytes: number;
  consentimiento: boolean;
  estado_envio: EstadoEnvio;
  enviado_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PresignedUrl {
  url: string;
  expires_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface ApiErrorBody {
  error?: { code?: string; message?: string; details?: unknown };
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string | null;
  user_email: string | null;
  user_rol: string | null;
  user_sede: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  success: boolean;
  ip: string | null;
  user_agent: string | null;
  details: Record<string, unknown> | null;
}
