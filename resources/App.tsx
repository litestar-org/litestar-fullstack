import { Route, Routes, useLocation, useNavigate } from "react-router-dom"
// pages imports
import ProtectedRoutes from "@/lib/protected-routes"
import Placeholder from "@/pages/Placeholder"
import Login from "@/pages/access/Login"
import Register from "@/pages/access/Register"
import Home from "@/pages/Home"
import PageNotFound from "@/pages/PageNotFound"
import { useAuth } from "@/contexts/AuthProvider"
import { useEffect } from "react"
import { ThemeProvider } from "@/components/theme-provider"

const App: React.FC = () => {
  const navigate = useNavigate()
  const { auth } = useAuth()
  const { pathname } = useLocation()

  useEffect(() => {
    if (auth?.token && (pathname === "/login" || pathname === "/register")) {
      navigate("/")
    }
  }, [auth, pathname])

  return (
    <ThemeProvider defaultTheme="light" storageKey="dma-ui-theme">
      <Routes>
        <Route path="/" element={<ProtectedRoutes />}>
          <Route index element={<Home />} />
        </Route>
        <Route path="/landing" element={<Placeholder />} />
        <Route path="/terms" element={<Placeholder />} />
        <Route path="/privacy" element={<Placeholder />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<PageNotFound />} />
      </Routes>
    </ThemeProvider>
  )
}

export default App
