import { SEDES, SEDE_LABEL } from "@/lib/enums";
import type { EstadoEnvio, Sede } from "@/types/api";

export interface Filters {
  sede: Sede | "";
  desde: string;
  hasta: string;
  estado_envio: EstadoEnvio | "";
}

interface Props {
  value: Filters;
  onChange: (next: Filters) => void;
  showSede?: boolean;
}

export function FiltersBar({ value, onChange, showSede = true }: Props) {
  const set = <K extends keyof Filters>(k: K, v: Filters[K]) =>
    onChange({ ...value, [k]: v });

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {showSede && (
        <div>
          <label className="label">Sede</label>
          <select
            className="field"
            value={value.sede}
            onChange={(e) => set("sede", e.target.value as Sede | "")}
          >
            <option value="">Todas</option>
            {SEDES.map((s) => (
              <option key={s} value={s}>
                {SEDE_LABEL[s]}
              </option>
            ))}
          </select>
        </div>
      )}
      <div>
        <label className="label">Desde</label>
        <input
          type="date"
          className="field"
          value={value.desde}
          onChange={(e) => set("desde", e.target.value)}
        />
      </div>
      <div>
        <label className="label">Hasta</label>
        <input
          type="date"
          className="field"
          value={value.hasta}
          onChange={(e) => set("hasta", e.target.value)}
        />
      </div>
      <div>
        <label className="label">Estado envío</label>
        <select
          className="field"
          value={value.estado_envio}
          onChange={(e) =>
            set("estado_envio", e.target.value as EstadoEnvio | "")
          }
        >
          <option value="">Todos</option>
          <option value="pendiente">Pendiente</option>
          <option value="enviado">Enviado</option>
          <option value="fallido">Fallido</option>
        </select>
      </div>
    </div>
  );
}
