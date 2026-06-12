import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listAuditoria } from "@/api/auditoria";
import { extractApiError } from "@/api/client";
import { Pagination } from "@/components/Pagination";
import { formatDateTime } from "@/lib/format";

const PAGE_SIZE = 30;

const ACTIONS = [
  "", "login", "login_failed",
  "create_alta", "update_alta", "mark_sent_alta",
  "create_examen", "update_examen", "download_examen", "mark_sent_examen",
  "update_propietario", "update_mascota",
  "create_user", "update_user", "deactivate_user",
];

export function AuditoriaPage() {
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const [success, setSuccess] = useState<"" | "true" | "false">("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");

  const q = useQuery({
    queryKey: ["auditoria", page, action, success, desde, hasta],
    queryFn: () =>
      listAuditoria({
        page,
        size: PAGE_SIZE,
        action: action || undefined,
        success: success === "" ? undefined : success === "true",
        desde: desde || undefined,
        hasta: hasta || undefined,
      }),
    placeholderData: (prev) => prev,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-800">Auditoría</h2>
      </div>

      <div className="card grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label className="label">Acción</label>
          <select
            className="field"
            value={action}
            onChange={(e) => { setPage(1); setAction(e.target.value); }}
          >
            {ACTIONS.map((a) => (
              <option key={a || "all"} value={a}>{a || "Todas"}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Resultado</label>
          <select
            className="field"
            value={success}
            onChange={(e) => { setPage(1); setSuccess(e.target.value as "" | "true" | "false"); }}
          >
            <option value="">Todos</option>
            <option value="true">Éxito</option>
            <option value="false">Falla</option>
          </select>
        </div>
        <div>
          <label className="label">Desde</label>
          <input
            type="date" className="field"
            value={desde} onChange={(e) => { setPage(1); setDesde(e.target.value); }}
          />
        </div>
        <div>
          <label className="label">Hasta</label>
          <input
            type="date" className="field"
            value={hasta} onChange={(e) => { setPage(1); setHasta(e.target.value); }}
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-slate-200">
        {q.isError && (
          <div className="bg-red-50 px-4 py-3 text-sm text-red-700">
            {extractApiError(q.error)}
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <Th>Cuándo</Th>
                <Th>Quién</Th>
                <Th>Acción</Th>
                <Th>Recurso</Th>
                <Th>OK</Th>
                <Th>IP</Th>
                <Th>Detalles</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {q.isLoading && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                    Cargando…
                  </td>
                </tr>
              )}
              {q.data?.items.length === 0 && !q.isLoading && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                    Sin eventos con esos filtros.
                  </td>
                </tr>
              )}
              {q.data?.items.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50 align-top">
                  <Td>{formatDateTime(e.timestamp)}</Td>
                  <Td>
                    <span className="block">{e.user_email ?? "—"}</span>
                    <span className="text-xs text-slate-500">
                      {e.user_rol ?? ""}
                      {e.user_sede ? ` · ${e.user_sede}` : ""}
                    </span>
                  </Td>
                  <Td>
                    <code className="text-xs">{e.action}</code>
                  </Td>
                  <Td>
                    {e.resource_type ? (
                      <span>
                        {e.resource_type}
                        {e.resource_id && (
                          <span className="block text-xs text-slate-500">
                            {e.resource_id.slice(0, 8)}…
                          </span>
                        )}
                      </span>
                    ) : "—"}
                  </Td>
                  <Td>
                    {e.success ? (
                      <span className="badge bg-emerald-100 text-emerald-800">OK</span>
                    ) : (
                      <span className="badge bg-red-100 text-red-800">Falló</span>
                    )}
                  </Td>
                  <Td><code className="text-xs">{e.ip ?? "—"}</code></Td>
                  <Td>
                    {e.details ? (
                      <pre className="max-w-md whitespace-pre-wrap break-words text-xs text-slate-600">
                        {JSON.stringify(e.details, null, 2)}
                      </pre>
                    ) : "—"}
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {q.data && (
          <Pagination
            page={q.data.page}
            size={q.data.size}
            total={q.data.total}
            onPageChange={setPage}
          />
        )}
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
      {children}
    </th>
  );
}
function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-3 py-3 text-slate-700">{children}</td>;
}
