import clsx from "clsx";
import { forwardRef } from "react";

interface Props
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  hasError?: boolean;
}

export const WhatsAppInput = forwardRef<HTMLInputElement, Props>(
  function WhatsAppInput({ hasError, className, ...rest }, ref) {
    return (
      <div>
        <div className="flex">
          <span className="inline-flex items-center rounded-l-md border border-r-0 border-slate-300 bg-slate-50 px-3 text-sm text-slate-500">
            🇪🇨
          </span>
          <input
            ref={ref}
            type="tel"
            autoComplete="tel"
            inputMode="tel"
            placeholder="+593 99 123 4567"
            className={clsx(
              "field rounded-l-none",
              hasError && "field-error",
              className,
            )}
            {...rest}
          />
        </div>
        <p className="mt-1 text-xs text-slate-500">
          Incluye código de país (ej. <code>+593...</code>). Solo dígitos, espacios o guiones.
        </p>
      </div>
    );
  },
);
