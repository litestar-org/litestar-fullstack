import { createRoot, hydrateRoot } from "react-dom/client"
import { createInertiaApp } from "@inertiajs/react"
import { resolvePageComponent } from "litestar-vite-plugin/inertia-helpers"
import { ThemeProvider } from "@/components/theme-provider"
import axios from "axios"
import "./main.css"
const appName = import.meta.env.VITE_APP_NAME || "Fullstack"
axios.defaults.withCredentials = true
createInertiaApp({
  title: (title) => `${title} - ${appName}`,
  resolve: (name) =>
    resolvePageComponent(
      `./pages/${name}.tsx`,
      import.meta.glob("./pages/**/*.tsx")
    ),
  setup({ el, App, props }) {
    const appElement = (
      <ThemeProvider defaultTheme="system" storageKey="ui-theme">
        <App {...props} />
      </ThemeProvider>
    )
    if (import.meta.env.DEV) {
      createRoot(el).render(appElement)
      return
    }

    hydrateRoot(el, appElement)
  },
  progress: {
    color: "#4B5563",
  },
})
