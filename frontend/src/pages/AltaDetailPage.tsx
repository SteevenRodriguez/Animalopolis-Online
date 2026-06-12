import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { getAlta } from "@/api/altas";
import { extractApiError } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { EstadoEnvioBadge } from "@/components/Badge";
import { SEDE_LABEL, TIPO_CONSULTA_LABEL } from "@/lib/enums";
import { formatDate, formatDateTime } from "@/lib/format";

export function AltaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const q = useQuery({
    queryKey: ["alta", id],
    queryFn: () => getAlta(id!),
    enabled: !!id,
  });
  const canEdit = user?.rol === "admin" || user?.rol === "staff";

  if (q.isLoading) return <div className="text-slate-500">Cargando…</div>;
  if (q.isError) {
    return (
      <div className="card text-red-700">
        {extractApiError(q.error, "No se pudo cargar el alta")}
      </div>
    );
  }
  const a = q.data!;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-xl font-semibold text-slate-800">Detalle de alta</h2>
        <div className="flex gap-2">
          {canEdit && (
            <Link to={`/altas/${a.id}/editar`} className="btn-secondary">
              Editar
            </Link>
          )}
          <Link to="/altas" className="btn-secondary">← Volver</Link>
        </div>
      </div>
      <div className="card grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Sede" value={SEDE_LABEL[a.sede]} />
        <Field label="Fecha de atención" value={formatDate(a.fecha_atencion)} />
        <Field label="Tipo de consulta" value={TIPO_CONSULTA_LABEL[a.tipo_consulta]} />
        <Field label="Estado de envío" value={<EstadoEnvioBadge value={a.estado_envio} />} />
        <Field label="Consentimiento" value={a.consentimiento ? "Sí" : "No"} />
        <Field label="Enviado el" value={formatDateTime(a.enviado_at)} />
        <Field label="Creado" value={formatDateTime(a.created_at)} />
        <Field label="ID" value={<code className="text-xs">{a.id}</code>} />
      </div>
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
