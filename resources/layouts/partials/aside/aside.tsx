import React, { PropsWithChildren } from "react"
import { route } from "litestar-vite-plugin/inertia-helpers"

import { InertiaLinkProps, Link } from "@inertiajs/react"
import { cn } from "@/lib/utils"
import {
  KanbanSquareDashedIcon,
  LayoutDashboardIcon,
  NotebookIcon,
  PersonStandingIcon,
  SettingsIcon,
} from "lucide-react"

export function Aside() {
  return (
    <ul className="grid items-start px-2 text-sm font-medium lg:px-4">
      <AsideLink
        active={route("dashboard") == window.location.toString()}
        href={route("dashboard")}
      >
        <KanbanSquareDashedIcon />
        <span>Dashboard</span>
      </AsideLink>
      <AsideLink
        active={route("profile.edit") == window.location.toString()}
        href={route("profile.edit")}
      >
        <SettingsIcon />
        <span>Settings</span>
      </AsideLink>
      <AsideLink
        active={route("users.*") == window.location.toString()}
        href={route("users.index")}
      >
        <PersonStandingIcon />
        Users
      </AsideLink>
      <AsideLink
        active={route("articles.*") == window.location.toString()}
        href={route("articles.index")}
      >
        <NotebookIcon />
        Articles
      </AsideLink>
      <AsideLink
        active={route("categories.*") == window.location.toString()}
        href={route("categories.index")}
      >
        <LayoutDashboardIcon />
        Categories
      </AsideLink>
    </ul>
  )
}

interface AsideLinkProps extends InertiaLinkProps {
  className?: string
  active?: boolean
}

export function AsideLink({ className, active, ...props }: AsideLinkProps) {
  return (
    <li className="-mx-1">
      <Link
        className={cn(
          active ? "text-foreground font-semibold" : "text-muted-foreground",
          "flex items-center [&>svg]:size-4 [&>svg]:stroke-[1.25] [&>svg]:mr-2 [&>svg]:-ml-1 hover:bg-accent/50 tracking-tight text-sm hover:text-foreground px-4 py-2 rounded-md"
        )}
        {...props}
      />
    </li>
  )
}

export function AsideLabel({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <li className="-mx-4">
      <span
        className={cn(
          "flex items-center text-muted-foreground [&>svg]:w-4 [&>svg]:stroke-[1.25] [&>svg]:h-4 [&>svg]:mr-3 tracking-tight text-sm px-4 py-2 rounded-md",
          className
        )}
      >
        {children}
      </span>
    </li>
  )
}
