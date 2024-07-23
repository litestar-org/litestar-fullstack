import { Link, router, usePage } from "@inertiajs/react"
import { Logo } from "@/components/logo"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarImage } from "@/components/ui/avatar"
import { getFirstWord, getGravatarUrl, strLimit } from "@/lib/utils"
import { route } from "litestar-vite-plugin/inertia-helpers"

import {
  ChevronDownIcon,
  CircleUserIcon,
  LogOutIcon,
  UserRoundCogIcon,
} from "lucide-react"

const ResponsiveNavbar = () => {
  const { auth } = usePage<InertiaProps>().props
  return (
    <nav className="block border-b px-4 py-2 sm:hidden">
      <div className="flex items-center justify-between py-1">
        <Link href="/">
          <Logo className="w-8 fill-red-600" />
        </Link>
        <div className="flex items-center gap-x-1">
          <DropdownMenu>
            <DropdownMenuTrigger asChild className="focus:outline-none">
              <button className="flex items-center focus:outline-none">
                {auth?.user?.id
                  ? getFirstWord(auth?.user.name ?? auth.user.email)
                  : "Menu"}
                <ChevronDownIcon className="ml-2 size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="mr-8 w-72">
              {auth?.user && (
                <>
                  <DropdownMenuLabel>
                    <div className="flex items-center font-normal">
                      <Avatar>
                        <AvatarImage
                          src={
                            auth.user.avatarUrl ??
                            getGravatarUrl(auth.user.email)
                          }
                          alt={auth?.user.name ?? auth.user.email}
                        />
                      </Avatar>
                      <div className="ml-3">
                        <strong className="font-semibold text-primary">
                          {auth.user.name}
                        </strong>
                        <div className="text-muted-foreground">
                          {strLimit(auth.user.email, 28)}
                        </div>
                      </div>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                </>
              )}
              <DropdownMenuItem asChild>
                <Link href={route("home")}>Home</Link>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Link href={route("about")}>About</Link>
              </DropdownMenuItem>
              {auth?.user ? (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <Link href={route("dashboard")}>Dashboard</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="flex justify-between items-center"
                    asChild
                  >
                    <Link href={route("profile.show")}>
                      Profile
                      <UserRoundCogIcon className="size-4" />
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => router.post(route("logout"))}
                  >
                    <span>Logout</span>
                  </DropdownMenuItem>
                </>
              ) : (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link className="flex items-center" href={route("login")}>
                      <LogOutIcon className="rotate-180 mr-2 size-4" />
                      <span>Login</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link
                      className="flex items-center"
                      href={route("register")}
                    >
                      <CircleUserIcon className="mr-2 size-4" />
                      <span>Register</span>
                    </Link>
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  )
}

export default ResponsiveNavbar
