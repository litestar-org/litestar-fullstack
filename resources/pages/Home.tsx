import { useAuth } from "@/contexts/AuthProvider"
import MainLayout from "@/layouts/MainLayout"
import { useEffect, useState } from "react"

const Home: React.FC = () => {
  const { auth } = useAuth()
  const [fetching, setFetching] = useState(false)

  useEffect(() => {}, [auth?.token])

  return (
    <MainLayout
      title="Litestar Application - Home"
      description="Litestar Application - Home"
      keywords="home"
    >
      <div className="h-screen w-full flex justify-center items-center bg-blue-900/20 pt-24">
        <div className="h-full w-full md:w-[70%] mx-auto flex flex-col items-center"></div>
      </div>
    </MainLayout>
  )
}

export default Home
