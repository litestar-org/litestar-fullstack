import { Outlet } from "@tanstack/react-router"
import { Link } from "@tanstack/react-router"

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold">
            Litestar App
          </Link>
          <nav className="flex items-center gap-4">
            <Link to="/login" className="text-sm hover:text-primary">
              Login
            </Link>
            <Link to="/signup" className="text-sm hover:text-primary">
              Sign Up
            </Link>
          </nav>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
