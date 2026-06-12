import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { z } from "zod";
import { getAlta, updateAlta } from "@/api/altas";
import { extractApiError } from "@/api/client";
import {
  TIPOS_CONSULTA,
  TIPO_CONSULTA_LABEL,
} from "@/lib/enums";

const schema = z.object({
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
});

type FormValues = z.infer<typeof schema>;

export function AltaEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const q = useQuery({
    queryKey: ["alta", id],
    queryFn: () => getAlta(id!),
    enabled: !!id,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (q.data) {
      reset({
        fecha_atencion: q.data.fecha_atencion,
        tipo_consulta: q.data.tipo_consulta,
      });
    }
  }, [q.data, reset]);

  const mutation = useMutation({
    mutationFn: (v: FormValues) => updateAlta(id!, v),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["altas"] });
      queryClient.invalidateQueries({ queryKey: ["alta", id] });
      navigate(`/altas/${id}`);
    },
  });

  if (q.isLoading) return <div className="text-slate-500">Cargando…</div>;
  if (q.isError || !q.data) {
    return (
      <div className="card text-red-700">
        {extractApiError(q.error, "No se pudo cargar el alta")}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-slate-800">Editar alta</h2>
      <form
        onSubmit={handleSubmit((v) => mutation.mutate(v))}
        className="card space-y-4"
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Fecha de atención</label>
            <input type="date" className="field" {...register("fecha_atencion")} />
            {errors.fecha_atencion && (
              <p className="mt-1 text-xs text-red-600">{errors.fecha_atencion.message}</p>
            )}
          </div>
          <div>
            <label className="label">Tipo de consulta</label>
            <select className="field" {...register("tipo_consulta")}>
              {TIPOS_CONSULTA.map((t) => (
                <option key={t} value={t}>{TIPO_CONSULTA_LABEL[t]}</option>
              ))}
            </select>
          </div>
        </div>

        <p className="text-xs text-slate-500">
          La sede, mascota, propietario y consentimiento no son editables.
          Para cambios mayores, crea un nuevo registro.
        </p>

        {mutation.isError && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {extractApiError(mutation.error)}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate(`/altas/${id}`)}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={isSubmitting || mutation.isPending}
          >
            {mutation.isPending ? "Guardando…" : "Guardar cambios"}
          </button>
        </div>
      </form>
    </div>
  );
}
