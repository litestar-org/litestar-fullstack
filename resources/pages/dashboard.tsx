import { Head, usePage } from "@inertiajs/react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { AppLayout } from "@/layouts/app-layout"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { PagePropsData } from "@/types"

export default function Dashboard() {
  const { auth } = usePage<PagePropsData>().props
  return (
    <>
      <Head title="Dashboard" />
      <Header title="Dashboard" />
      <Container>
        <Card>
          <CardHeader>
            <CardTitle>Dashboard</CardTitle>
            <CardDescription>
              Hi {auth?.user?.name}, you are now logged in.
            </CardDescription>
          </CardHeader>
          <CardContent>
            Hi {auth?.user?.name}, you are now logged in.
            <div className="mb-2 text-muted-foreground">
              // The page you are currently visiting is
            </div>
            <div className="text-lime-600 dark:text-lime-400">
              "resources/pages/Dashboard.tsx"
            </div>
          </CardContent>
        </Card>
      </Container>
    </>
  )
}

Dashboard.layout = (page: any) => <AppLayout children={page} />
