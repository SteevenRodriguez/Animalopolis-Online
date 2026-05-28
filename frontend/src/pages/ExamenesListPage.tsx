import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useState } from "react";
import { listExamenes } from "@/api/examenes";
import { extractApiError } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { EstadoEnvioBadge } from "@/components/Badge";
import { FiltersBar, type Filters } from "@/components/FiltersBar";
import { Pagination } from "@/components/Pagination";
import { SEDE_LABEL, TIPO_EXAMEN_LABEL } from "@/lib/enums";
import { formatBytes, formatDateTime } from "@/lib/format";

const PAGE_SIZE = 20;

export function ExamenesListPage() {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Filters>({
    sede: "",
    desde: "",
    hasta: "",
    estado_envio: "",
  });

  const query = useQuery({
    queryKey: ["examenes", page, filters],
    queryFn: () =>
      listExamenes({
        page,
        size: PAGE_SIZE,
        sede: filters.sede || undefined,
        desde: filters.desde || undefined,
        hasta: filters.hasta || undefined,
        estado_envio: filters.estado_envio || undefined,
      }),
    placeholderData: (prev) => prev,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-800">Exámenes</h2>
        <Link to="/examenes/nuevo" className="btn-primary">
          + Cargar examen
        </Link>
      </div>

      <div className="card">
        <FiltersBar
          value={filters}
          onChange={(f) => {
            setPage(1);
            setFilters(f);
          }}
          showSede={user?.rol === "admin"}
        />
      </div>

      <div className="overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-slate-200">
        {query.isError && (
          <div className="bg-red-50 px-4 py-3 text-sm text-red-700">
            {extractApiError(query.error)}
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <Th>Fecha</Th>
                <Th>Sede</Th>
                <Th>Tipo</Th>
                <Th>Archivo</Th>
                <Th>Estado</Th>
                <Th> </Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {query.isLoading && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-sm text-slate-500">
                    Cargando…
                  </td>
                </tr>
              )}
              {query.data?.items.length === 0 && !query.isLoading && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-sm text-slate-500">
                    No hay exámenes con esos filtros.
                  </td>
                </tr>
              )}
              {query.data?.items.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50">
                  <Td>{formatDateTime(e.created_at)}</Td>
                  <Td>{SEDE_LABEL[e.sede]}</Td>
                  <Td>{TIPO_EXAMEN_LABEL[e.tipo_examen]}</Td>
                  <Td>
                    <span className="block max-w-xs truncate text-sm" title={e.archivo_nombre}>
                      {e.archivo_nombre}
                    </span>
                    <span className="text-xs text-slate-500">
                      {e.archivo_mime} · {formatBytes(e.archivo_size_bytes)}
                    </span>
                  </Td>
                  <Td>
                    <EstadoEnvioBadge value={e.estado_envio} />
                  </Td>
                  <Td>
                    <Link
                      to={`/examenes/${e.id}`}
                      className="text-brand-600 hover:underline"
                    >
                      Ver
                    </Link>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {query.data && (
          <Pagination
            page={query.data.page}
            size={query.data.size}
            total={query.data.total}
            onPageChange={setPage}
          />
        )}
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
      {children}
    </th>
  );
}
function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-4 py-3 text-sm text-slate-700">{children}</td>;
}
