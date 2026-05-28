import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createExamen } from "@/api/examenes";
import { extractApiError } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { FileUpload } from "@/components/FileUpload";
import { WhatsAppInput } from "@/components/WhatsAppInput";
import {
  SEDES,
  SEDE_LABEL,
  TIPOS_EXAMEN,
  TIPO_EXAMEN_LABEL,
} from "@/lib/enums";
import type { Sede, TipoExamen } from "@/types/api";

const schema = z.object({
  sede: z.enum(["urdesa", "ciudad_celeste"]),
  nombre_mascota: z.string().min(1, "Requerido").max(255),
  nombre_propietario: z.string().min(1, "Requerido").max(255),
  whatsapp: z
    .string()
    .min(4)
    .max(32)
    .regex(/^[+0-9\s-]+$/, "Solo dígitos, espacios o guiones"),
  tipo_examen: z.enum([
    "sangre",
    "orina",
    "heces",
    "radiografia",
    "ecografia",
    "citologia",
    "otro",
  ]),
  consentimiento: z.literal(true, {
    errorMap: () => ({ message: "Debes aceptar el consentimiento" }),
  }),
});

type FormValues = z.infer<typeof schema>;

export function ExamenFormPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      sede: (user?.sede ?? "urdesa") as Sede,
      tipo_examen: "sangre" as TipoExamen,
      consentimiento: undefined as unknown as true,
    },
  });

  const mutation = useMutation({
    mutationFn: (v: FormValues) =>
      createExamen({ ...v, file: file as File }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["examenes"] });
      navigate(`/examenes/${created.id}`);
    },
  });

  const sedeDisabled = user?.rol === "staff";

  function onSubmit(v: FormValues) {
    if (!file) {
      setFileError("Adjunta un archivo del examen.");
      return;
    }
    setFileError(null);
    mutation.mutate(v);
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-slate-800">Cargar examen</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Sede</label>
            <select className="field" disabled={sedeDisabled} {...register("sede")}>
              {SEDES.map((s) => (
                <option key={s} value={s}>{SEDE_LABEL[s]}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Tipo de examen</label>
            <select className="field" {...register("tipo_examen")}>
              {TIPOS_EXAMEN.map((t) => (
                <option key={t} value={t}>{TIPO_EXAMEN_LABEL[t]}</option>
              ))}
            </select>
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
        </div>

        <div>
          <label className="label">Archivo del examen</label>
          <FileUpload value={file} onChange={setFile} hasError={!!fileError} />
          {fileError && <p className="mt-1 text-xs text-red-600">{fileError}</p>}
        </div>

        <label className="flex items-start gap-3 rounded-md bg-slate-50 p-3 text-sm">
          <input type="checkbox" className="mt-0.5" {...register("consentimiento")} />
          <span>
            El propietario otorga su consentimiento informado para procesar y
            comunicar este examen.
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
          <button
            type="submit"
            className="btn-primary"
            disabled={isSubmitting || mutation.isPending}
          >
            {mutation.isPending ? "Subiendo…" : "Subir examen"}
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
