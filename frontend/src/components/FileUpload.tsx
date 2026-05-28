import clsx from "clsx";
import { useRef, useState } from "react";
import { formatBytes } from "@/lib/format";

const ACCEPT = "application/pdf,image/jpeg,image/png,image/webp";
const ACCEPT_DESC = "PDF, JPG, PNG o WEBP";

interface Props {
  value: File | null;
  onChange: (file: File | null) => void;
  maxSizeBytes?: number;
  hasError?: boolean;
}

export function FileUpload({
  value,
  onChange,
  maxSizeBytes = 15 * 1024 * 1024,
  hasError,
}: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  function handlePick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    if (!f) {
      onChange(null);
      return;
    }
    if (!ACCEPT.split(",").includes(f.type)) {
      setLocalError(`Tipo no permitido. Solo ${ACCEPT_DESC}.`);
      onChange(null);
      return;
    }
    if (f.size > maxSizeBytes) {
      setLocalError(`Archivo demasiado grande (máx ${formatBytes(maxSizeBytes)}).`);
      onChange(null);
      return;
    }
    setLocalError(null);
    onChange(f);
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={handlePick}
      />
      <div
        className={clsx(
          "rounded-md border-2 border-dashed px-4 py-6 text-center",
          hasError || localError
            ? "border-red-400 bg-red-50"
            : "border-slate-300 bg-slate-50",
        )}
      >
        {value ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-700">{value.name}</p>
            <p className="text-xs text-slate-500">
              {value.type} · {formatBytes(value.size)}
            </p>
            <div className="flex justify-center gap-2">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => inputRef.current?.click()}
              >
                Cambiar
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => onChange(null)}
              >
                Quitar
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-slate-600">
              Arrastra un archivo o
            </p>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => inputRef.current?.click()}
            >
              Seleccionar archivo
            </button>
            <p className="text-xs text-slate-500">{ACCEPT_DESC} · máx {formatBytes(maxSizeBytes)}</p>
          </div>
        )}
      </div>
      {localError && (
        <p className="mt-1 text-xs text-red-600">{localError}</p>
      )}
    </div>
  );
}
