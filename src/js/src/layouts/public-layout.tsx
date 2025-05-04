import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme-context";
import { Outlet } from "@tanstack/react-router";
import { Link } from "@tanstack/react-router";
import { Moon, Sun } from "lucide-react";

export function PublicLayout() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b border-border">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold">
            <div className="flex items-center text-lg font-medium">
              <img src={theme === "dark" ? "images/logo-light.svg" : "images/logo-dark.svg"} alt="Litestar Logo" className="h-8 mr-3" />
              Litestar App
            </div>
          </Link>
          <Button variant="ghost" size="icon" onClick={toggleTheme} className="hover:bg-accent hover:text-accent-foreground hover:cursor-pointer">
            {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
          </Button>
        </div>
      </header>
      <main className="flex-1 flex">
        <Outlet />
      </main>
    </div>
  );
}
