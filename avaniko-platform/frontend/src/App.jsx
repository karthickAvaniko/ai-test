import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { useAuth } from "./store/auth";
import { useEffect } from "react";
import Login     from "./pages/Login";
import Signup    from "./pages/Signup";
import Dashboard from "./pages/Dashboard";

function PrivateRoute({ children }) {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" replace />;
}

// ✅ Listens for auth:logout event (fired by api.js on 401) and navigates via React Router
function AuthLogoutListener() {
  const { logout } = useAuth();
  const navigate   = useNavigate();
  useEffect(() => {
    const handle = () => { logout(); navigate("/login", { replace: true }); };
    window.addEventListener("auth:logout", handle);
    return () => window.removeEventListener("auth:logout", handle);
  }, [logout, navigate]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthLogoutListener />
      <Toaster position="top-right" toastOptions={{ style: { background: "#1a1a1a", color: "#fff", border: "1px solid #333" } }} />
      <Routes>
        <Route path="/login"       element={<Login />} />
        <Route path="/signup"      element={<Signup />} />
        <Route path="/dashboard/*" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="*"            element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
