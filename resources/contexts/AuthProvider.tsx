import { toast } from "@/components/ui/use-toast"
import axios from "axios"
import { jwtDecode } from "jwt-decode"
import { createContext, useContext, useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

type User = {
  id: string
  name: string
  email: string
  createdAt: string
}

interface handleLoginProps {
  token: string
  user: User | null
}

interface AuthStateProps {
  user: User | null
  token: string
}

const AuthContext = createContext<null | any>(null)

export const useAuth = () => {
  return useContext(AuthContext)
}

const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate()
  const [auth, setAuth] = useState<AuthStateProps>({
    user: null,
    token: "",
  })

  axios.defaults.headers.common["Authorization"] = auth?.token || ""

  useEffect(() => {
    const storedAuth = JSON.parse(localStorage.getItem("auth")!)
    if (storedAuth) {
      const decodedToken = jwtDecode(storedAuth.token)
      const expiresAt = decodedToken?.exp
      const currentTime = Math.floor(Date.now() / 1000)
      if (expiresAt! <= currentTime) {
        setAuth({ user: null, token: "" })
        localStorage.removeItem("auth")
        return
      } else {
        setAuth({
          user: storedAuth.user,
          token: storedAuth.token,
        })
      }
    }
  }, [])

  const handleLogin = ({ token, user }: handleLoginProps) => {
    setAuth({ user, token })
    localStorage.setItem("auth", JSON.stringify({ user, token }))
    return
  }

  const handleLogout = () => {
    setAuth({ user: null, token: "" })
    localStorage.removeItem("auth")
    toast({
      title: "Logged out successfully",
    })
    navigate("/login")
    return
  }

  return (
    <AuthContext.Provider
      value={{
        auth,
        setAuth,
        handleLogin,
        handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider
