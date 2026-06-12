import { NavLink, Outlet, useNavigate } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "@/auth/AuthContext";
import { ROL_LABEL, SEDE_LABEL } from "@/lib/enums";

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  const canWrite = user?.rol === "admin" || user?.rol === "staff";
  const isAdmin = user?.rol === "admin";

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-navy text-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Animalópolis" className="h-7 w-auto" />
            <p className="text-xs text-slate-300">
              {user?.nombre} · {user ? ROL_LABEL[user.rol] : ""}
              {user?.sede ? ` · ${SEDE_LABEL[user.sede]}` : " · todas las sedes"}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="btn self-start border border-navy-light bg-navy-light text-white hover:bg-navy-dark sm:self-auto"
          >
            Cerrar sesión
          </button>
        </div>
        <nav className="border-t border-navy-light">
          <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-2 py-2">
            <NavTab to="/altas">Altas</NavTab>
            {canWrite && <NavTab to="/altas/nueva">+ Nueva alta</NavTab>}
            <NavTab to="/examenes">Exámenes</NavTab>
            {canWrite && <NavTab to="/examenes/nuevo">+ Cargar examen</NavTab>}
            {isAdmin && <NavTab to="/auditoria">Auditoría</NavTab>}
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}

function NavTab({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        clsx(
          "rounded-md px-3 py-2 text-sm font-medium whitespace-nowrap",
          isActive
            ? "bg-navy-light text-accent-400"
            : "text-slate-200 hover:bg-navy-light hover:text-white",
        )
      }
    >
      {children}
    </NavLink>
  );
}
