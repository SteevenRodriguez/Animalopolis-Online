import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { getExamen, getExamenFileUrl } from "@/api/examenes";
import { extractApiError } from "@/api/client";
import { EstadoEnvioBadge } from "@/components/Badge";
import { SEDE_LABEL, TIPO_EXAMEN_LABEL } from "@/lib/enums";
import { formatBytes, formatDateTime } from "@/lib/format";

export function ExamenDetailPage() {
  const { id } = useParams<{ id: string }>();
  const q = useQuery({
    queryKey: ["examen", id],
    queryFn: () => getExamen(id!),
    enabled: !!id,
  });

  const urlMutation = useMutation({
    mutationFn: () => getExamenFileUrl(id!),
    onSuccess: (resp) => {
      window.open(resp.url, "_blank", "noopener,noreferrer");
    },
  });

  if (q.isLoading) return <div className="text-slate-500">Cargando…</div>;
  if (q.isError) {
    return (
      <div className="card text-red-700">
        {extractApiError(q.error, "No se pudo cargar el examen")}
      </div>
    );
  }
  const e = q.data!;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-800">Detalle de examen</h2>
        <Link to="/examenes" className="btn-secondary">← Volver</Link>
      </div>
      <div className="card grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Sede" value={SEDE_LABEL[e.sede]} />
        <Field label="Tipo" value={TIPO_EXAMEN_LABEL[e.tipo_examen]} />
        <Field label="Archivo" value={e.archivo_nombre} />
        <Field label="Tipo MIME" value={e.archivo_mime} />
        <Field label="Tamaño" value={formatBytes(e.archivo_size_bytes)} />
        <Field label="Estado de envío" value={<EstadoEnvioBadge value={e.estado_envio} />} />
        <Field label="Consentimiento" value={e.consentimiento ? "Sí" : "No"} />
        <Field label="Enviado el" value={formatDateTime(e.enviado_at)} />
        <Field label="Creado" value={formatDateTime(e.created_at)} />
        <Field label="ID" value={<code className="text-xs">{e.id}</code>} />
      </div>

      <div className="card flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-medium text-slate-800">Archivo en S3</p>
          <p className="text-sm text-slate-500">
            La URL es firmada y temporal — se abrirá en una pestaña nueva.
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => urlMutation.mutate()}
          disabled={urlMutation.isPending}
        >
          {urlMutation.isPending ? "Generando…" : "Ver archivo"}
        </button>
      </div>
      {urlMutation.isError && (
        <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {extractApiError(urlMutation.error)}
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm text-slate-800">{value}</dd>
    </div>
  );
}
