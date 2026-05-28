import clsx from "clsx";
import { ESTADO_ENVIO_BADGE, ESTADO_ENVIO_LABEL } from "@/lib/enums";
import type { EstadoEnvio } from "@/types/api";

export function EstadoEnvioBadge({ value }: { value: EstadoEnvio }) {
  return (
    <span className={clsx("badge", ESTADO_ENVIO_BADGE[value])}>
      {ESTADO_ENVIO_LABEL[value]}
    </span>
  );
}
