import { Route, Routes, useLocation, useNavigate } from "react-router-dom";
// pages imports
import ProtectedRoutes from "@/lib/protected-routes";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Home from "@/pages/Home";
import PageNotFound from "@/pages/PageNotFound";
import { useAuth } from "@/contexts/AuthProvider";
import { useEffect } from "react";

const App: React.FC = () => {
  const navigate = useNavigate();
  const { auth } = useAuth();
  const { pathname } = useLocation();

  useEffect(() => {
    if (auth?.token && (pathname === "/login" || pathname === "/register")) {
      navigate("/");
    }
  }, [auth, pathname]);

  return (
    <Routes>
      <Route path="/" element={<ProtectedRoutes />}>
        <Route index element={<Home />} />
      </Route>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="*" element={<PageNotFound />} />
    </Routes>
  );
};

export default App;
