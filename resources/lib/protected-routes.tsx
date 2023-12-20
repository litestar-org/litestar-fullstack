import { useAuth } from "@/contexts/AuthProvider"
import { useEffect } from "react"
import { Outlet, useNavigate } from "react-router-dom"

const ProtectedRoutes: React.FC = () => {
  const { auth } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!auth.user && !auth.token) {
      return navigate("/login")
    }
  }, [auth])

  return <Outlet />
}

export default ProtectedRoutes
