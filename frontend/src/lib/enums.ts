import type { EstadoEnvio, Sede, TipoConsulta, TipoExamen } from "@/types/api";

export const SEDE_LABEL: Record<Sede, string> = {
  urdesa: "Urdesa",
  ciudad_celeste: "Ciudad Celeste",
};

export const TIPO_CONSULTA_LABEL: Record<TipoConsulta, string> = {
  primera_consulta: "Primera consulta",
  control: "Control",
  vacunacion: "Vacunación",
  desparasitacion: "Desparasitación",
  emergencia: "Emergencia",
  cirugia: "Cirugía",
  otro: "Otro",
};

export const TIPO_EXAMEN_LABEL: Record<TipoExamen, string> = {
  sangre: "Sangre",
  orina: "Orina",
  heces: "Heces",
  radiografia: "Radiografía",
  ecografia: "Ecografía",
  citologia: "Citología",
  otro: "Otro",
};

export const ESTADO_ENVIO_LABEL: Record<EstadoEnvio, string> = {
  pendiente: "Pendiente",
  enviado: "Enviado",
  fallido: "Fallido",
};

export const ESTADO_ENVIO_BADGE: Record<EstadoEnvio, string> = {
  pendiente: "bg-amber-100 text-amber-800",
  enviado: "bg-emerald-100 text-emerald-800",
  fallido: "bg-red-100 text-red-800",
};

export const SEDES: Sede[] = ["urdesa", "ciudad_celeste"];
export const TIPOS_CONSULTA: TipoConsulta[] = [
  "primera_consulta",
  "control",
  "vacunacion",
  "desparasitacion",
  "emergencia",
  "cirugia",
  "otro",
];
export const TIPOS_EXAMEN: TipoExamen[] = [
  "sangre",
  "orina",
  "heces",
  "radiografia",
  "ecografia",
  "citologia",
  "otro",
];
