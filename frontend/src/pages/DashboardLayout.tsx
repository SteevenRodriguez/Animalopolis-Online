import { NavLink, Outlet, useNavigate } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "@/auth/AuthContext";
import { SEDE_LABEL } from "@/lib/enums";

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🐾</span>
            <div>
              <h1 className="text-lg font-semibold text-slate-800">Animalópolis</h1>
              <p className="text-xs text-slate-500">
                {user?.nombre} · {user?.rol}
                {user?.sede ? ` · ${SEDE_LABEL[user.sede]}` : " · todas las sedes"}
              </p>
            </div>
          </div>
          <button onClick={handleLogout} className="btn-secondary self-start sm:self-auto">
            Cerrar sesión
          </button>
        </div>
        <nav className="border-t border-slate-200">
          <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-2 py-2">
            <NavTab to="/altas">Altas</NavTab>
            <NavTab to="/altas/nueva">+ Nueva alta</NavTab>
            <NavTab to="/examenes">Exámenes</NavTab>
            <NavTab to="/examenes/nuevo">+ Cargar examen</NavTab>
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
            ? "bg-brand-50 text-brand-700"
            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
        )
      }
    >
      {children}
    </NavLink>
  );
}
