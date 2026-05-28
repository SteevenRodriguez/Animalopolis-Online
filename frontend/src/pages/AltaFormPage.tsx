import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createAlta } from "@/api/altas";
import { extractApiError } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { WhatsAppInput } from "@/components/WhatsAppInput";
import {
  SEDES,
  SEDE_LABEL,
  TIPOS_CONSULTA,
  TIPO_CONSULTA_LABEL,
} from "@/lib/enums";
import type { Sede, TipoConsulta } from "@/types/api";

const schema = z.object({
  sede: z.enum(["urdesa", "ciudad_celeste"]),
  nombre_mascota: z.string().min(1, "Requerido").max(255),
  nombre_propietario: z.string().min(1, "Requerido").max(255),
  whatsapp: z
    .string()
    .min(4, "WhatsApp muy corto")
    .max(32)
    .regex(/^[+0-9\s-]+$/, "Solo dígitos, espacios o guiones"),
  fecha_atencion: z.string().min(1, "Requerido"),
  tipo_consulta: z.enum([
    "primera_consulta",
    "control",
    "vacunacion",
    "desparasitacion",
    "emergencia",
    "cirugia",
    "otro",
  ]),
  consentimiento: z.literal(true, {
    errorMap: () => ({ message: "Debes aceptar el consentimiento" }),
  }),
});

type FormValues = z.infer<typeof schema>;

export function AltaFormPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const today = new Date().toISOString().slice(0, 10);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      sede: (user?.sede ?? "urdesa") as Sede,
      fecha_atencion: today,
      tipo_consulta: "control" as TipoConsulta,
      consentimiento: undefined as unknown as true,
    },
  });

  const mutation = useMutation({
    mutationFn: createAlta,
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["altas"] });
      navigate(`/altas/${created.id}`);
    },
  });

  const sedeDisabled = user?.rol === "staff";

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-slate-800">Nueva alta</h2>

      <form
        onSubmit={handleSubmit((v) => mutation.mutate(v))}
        className="card space-y-4"
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Sede</label>
            <select className="field" disabled={sedeDisabled} {...register("sede")}>
              {SEDES.map((s) => (
                <option key={s} value={s}>{SEDE_LABEL[s]}</option>
              ))}
            </select>
            {sedeDisabled && (
              <p className="mt-1 text-xs text-slate-500">
                Tu sede asignada. No editable.
              </p>
            )}
          </div>

          <div>
            <label className="label">Fecha de atención</label>
            <input type="date" className="field" {...register("fecha_atencion")} />
            <FieldError msg={errors.fecha_atencion?.message} />
          </div>

          <div>
            <label className="label">Nombre de la mascota</label>
            <input className="field" {...register("nombre_mascota")} />
            <FieldError msg={errors.nombre_mascota?.message} />
          </div>

          <div>
            <label className="label">Nombre del propietario</label>
            <input className="field" {...register("nombre_propietario")} />
            <FieldError msg={errors.nombre_propietario?.message} />
          </div>

          <div className="sm:col-span-2">
            <label className="label">WhatsApp del propietario</label>
            <WhatsAppInput
              {...register("whatsapp")}
              hasError={!!errors.whatsapp}
            />
            <FieldError msg={errors.whatsapp?.message} />
          </div>

          <div className="sm:col-span-2">
            <label className="label">Tipo de consulta</label>
            <select className="field" {...register("tipo_consulta")}>
              {TIPOS_CONSULTA.map((t) => (
                <option key={t} value={t}>{TIPO_CONSULTA_LABEL[t]}</option>
              ))}
            </select>
          </div>
        </div>

        <label className="flex items-start gap-3 rounded-md bg-slate-50 p-3 text-sm">
          <input type="checkbox" className="mt-0.5" {...register("consentimiento")} />
          <span>
            El propietario otorga su consentimiento informado para el tratamiento
            y comunicación de información clínica.
          </span>
        </label>
        <FieldError msg={errors.consentimiento?.message} />

        {mutation.isError && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {extractApiError(mutation.error)}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate(-1)}
          >
            Cancelar
          </button>
          <button type="submit" className="btn-primary" disabled={isSubmitting || mutation.isPending}>
            {isSubmitting || mutation.isPending ? "Guardando…" : "Guardar alta"}
          </button>
        </div>
      </form>
    </div>
  );
}

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null;
  return <p className="mt-1 text-xs text-red-600">{msg}</p>;
}
