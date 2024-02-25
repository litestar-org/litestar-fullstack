import { useAuth } from "@/contexts/AuthProvider"
import MainLayout from "@/layouts/MainLayout"
import { useEffect } from "react"
import { TeamSwitcher } from "@/components/team-switcher"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"

const Home: React.FC = () => {
  const { auth } = useAuth()

  useEffect(() => {}, [auth?.token])

  return (
    <MainLayout
      title="Litestar Application - Home"
      description="Litestar Application - Home"
      keywords="home"
    >
      <div className="hidden flex-col md:flex">
        <div className="border-b">
          <div className="flex h-16 items-center px-4">
            <MainNav className="mx-6" />
            <div className="ml-auto flex items-center space-x-4">
              <TeamSwitcher />
              <UserNav />
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  )
}

export default Home
