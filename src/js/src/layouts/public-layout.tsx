import { Outlet } from "@tanstack/react-router"

export function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex flex-1">
        <Outlet />
      </main>
    </div>
  )
}
