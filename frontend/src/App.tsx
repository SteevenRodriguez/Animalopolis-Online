import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/auth/AuthContext";
import { ProtectedRoute } from "@/auth/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardLayout } from "@/pages/DashboardLayout";
import { AltasListPage } from "@/pages/AltasListPage";
import { AltaDetailPage } from "@/pages/AltaDetailPage";
import { AltaEditPage } from "@/pages/AltaEditPage";
import { AltaFormPage } from "@/pages/AltaFormPage";
import { ExamenesListPage } from "@/pages/ExamenesListPage";
import { ExamenDetailPage } from "@/pages/ExamenDetailPage";
import { ExamenFormPage } from "@/pages/ExamenFormPage";
import { AuditoriaPage } from "@/pages/AuditoriaPage";

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/altas" replace />} />
          <Route path="/altas" element={<AltasListPage />} />
          <Route path="/altas/nueva" element={<AltaFormPage />} />
          <Route path="/altas/:id" element={<AltaDetailPage />} />
          <Route path="/altas/:id/editar" element={<AltaEditPage />} />
          <Route path="/examenes" element={<ExamenesListPage />} />
          <Route path="/examenes/nuevo" element={<ExamenFormPage />} />
          <Route path="/examenes/:id" element={<ExamenDetailPage />} />
          <Route
            path="/auditoria"
            element={
              <ProtectedRoute requireAdmin>
                <AuditoriaPage />
              </ProtectedRoute>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/altas" replace />} />
      </Routes>
    </AuthProvider>
  );
}
