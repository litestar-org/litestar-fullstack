import { InertiaLinkProps, Link, router, usePage } from "@inertiajs/react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import ResponsiveNavbar from "@/layouts/partials/responsive-navbar"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn, getGravatarUrl, getInitials } from "@/lib/utils"
import { LogInIcon, UserRoundCogIcon } from "lucide-react"
import { route } from "litestar-vite-plugin/inertia-helpers"
import { Icons } from "@/components/icons"
import { TeamSwitcher } from "@/components/team-switcher"

export default function Navbar() {
  const { auth } = usePage<InertiaProps>().props

  return (
    <>
      <ResponsiveNavbar />

      <nav className="relative bg-background z-10 hidden border-b py-3 sm:block">
        <div className="mx-auto max-w-screen-2xl items-center sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-x-4">
              <Link href="/" className="mr-3">
                <Icons.logo className="w-9 fill-foreground" />
              </Link>
              <NavLink
                active={isCurrentRoute("dashboard")}
                href={route("home")}
              >
                Home
              </NavLink>
              <NavLink
                active={isCurrentRoute("teams.*")}
                href={route("teams.list")}
              >
                Teams
              </NavLink>
              <NavLink active={isCurrentRoute("about")} href={route("about")}>
                About
              </NavLink>
            </div>
            {auth?.user ? (
              <>
                <div className="flex items-center gap-x-1">
                  <TeamSwitcher className="mr-5" />
                  <div className="mr-3 min-h-[1em] w-px self-stretch bg-gradient-to-tr from-transparent via-neutral-500 to-transparent opacity-25 dark:via-neutral-400" />
                  <DropdownMenu modal={false}>
                    <DropdownMenuTrigger asChild>
                      <Avatar className="size-8">
                        <AvatarImage
                          src={
                            auth.user.avatarUrl ??
                            getGravatarUrl(auth.user.email)
                          }
                        />
                        <AvatarFallback>
                          {getInitials(auth.user.email)}
                        </AvatarFallback>
                      </Avatar>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="mr-8 w-60">
                      <DropdownMenuLabel>
                        <div>{auth.user.name}</div>
                        <div className="text-muted-foreground font-normal text-sm">
                          {auth.user.email}
                        </div>
                      </DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem>
                        <Link
                          className="flex items-center w-full"
                          href={route("profile.show")}
                        >
                          <UserRoundCogIcon className="mr-2 size-4" />
                          Profile
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => router.post(route("logout"))}
                      >
                        Logout
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </>
            ) : (
              <>
                <DropdownMenu modal={false}>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="secondary"
                      className="bg-secondary/50 hover:bg-secondary/60 border"
                    >
                      Login
                      <LogInIcon className="ml-2 size-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="mr-8 w-40">
                    <DropdownMenuItem>
                      <Link href={route("login")}>Login</Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Link href={route("register")}>Register</Link>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            )}
          </div>
        </div>
      </nav>
    </>
  )
}

export function NavLink({
  active,
  ...props
}: InertiaLinkProps & {
  active?: boolean
}) {
  return (
    <Link
      {...props}
      className={cn(
        active ? "text-primary" : "text-muted-foreground",
        "px-3 py-2.5 text-sm font-medium transition-colors hover:text-primary"
      )}
    />
  )
}
