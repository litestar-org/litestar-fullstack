import { Link } from "@tanstack/react-router"
import { ChevronRight, type LucideIcon } from "lucide-react"

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarMenuSub, SidebarMenuSubButton, SidebarMenuSubItem } from "@/components/ui/sidebar"

interface NavLink {
  title: string
  to: string
}

export interface NavSection extends NavLink {
  icon?: LucideIcon
  subLinks?: NavLink[]
}

interface NavMainProps {
  sections: NavSection[]
}

export function NavMain({ sections }: Readonly<NavMainProps>) {
  return (
    <SidebarGroup>
      <SidebarGroupLabel>Platform</SidebarGroupLabel>
      <SidebarMenu>
        {sections.map((section) => {
          if (!section.subLinks || section.subLinks.length === 0) {
            return (
              <SidebarMenuItem key={section.title}>
                <SidebarMenuButton asChild tooltip={section.title}>
                  <Link to={section.to}>
                    {section.icon && <section.icon className="shrink-0" />}
                    <span className="group-data-[collapsible=icon]:hidden">{section.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          }

          return (
            <Collapsible key={section.title} asChild className="group/collapsible">
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  <SidebarMenuButton asChild tooltip={section.title}>
                    <Link to={section.to}>
                      {section.icon && <section.icon className="shrink-0" />}
                      <span className="group-data-[collapsible=icon]:hidden">{section.title}</span>
                      <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90 group-data-[collapsible=icon]:hidden" />
                    </Link>
                  </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <SidebarMenuSub>
                    {section.subLinks.map((subLink) => (
                      <SidebarMenuSubItem key={subLink.title}>
                        <SidebarMenuSubButton asChild>
                          <Link to={subLink.to}>
                            <span>{subLink.title}</span>
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    ))}
                  </SidebarMenuSub>
                </CollapsibleContent>
              </SidebarMenuItem>
            </Collapsible>
          )
        })}
      </SidebarMenu>
    </SidebarGroup>
  )
}
