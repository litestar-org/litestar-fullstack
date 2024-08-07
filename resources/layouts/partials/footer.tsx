import { ThemeToggle } from "@/components/theme-toggle"

export default function Footer() {
  return (
    <footer aria-labelledby="footer-heading" className="sticky top-full">
      <h2 id="footer-heading" className="sr-only">
        Footer
      </h2>
      <div className="h-full" />
      <div className="align-bottom mx-auto max-w-7xl px-6 pb-8 pt-20 ">
        <div className="border-t border-slate-900/10 md:flex md:items-center md:justify-between mb-5" />
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex space-x-6 md:order-2">
            <ThemeToggle />
          </div>
          <p className="mt-8 text-xs leading-5 text-muted-foreground md:order-1 md:mt-0">
            &copy; 2024{" "}
            <a
              href="https://litestar.dev/"
              className="font-semibold text-foreground"
            >
              Litestar
            </a>
            . All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
