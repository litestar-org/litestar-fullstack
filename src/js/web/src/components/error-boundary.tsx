import type { ErrorComponentProps } from "@tanstack/react-router"
import { useRouter } from "@tanstack/react-router"
import { AlertCircle, Home, RefreshCw } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function ErrorBoundary({ error, reset }: ErrorComponentProps) {
  const router = useRouter()

  const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred"

  return (
    <div className="flex min-h-screen w-full items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md border-border/60 bg-card/80 shadow-xl shadow-destructive/10">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <CardTitle>Something went wrong</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
          <div className="flex flex-col gap-2">
            <Button onClick={reset} variant="default" className="w-full">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try again
            </Button>
            <Button onClick={() => router.navigate({ to: "/" })} variant="outline" className="w-full">
              <Home className="mr-2 h-4 w-4" />
              Go to home
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
