import { Helmet, HelmetProvider } from "react-helmet-async"
import favicon from "@/assets/favicon.png"
interface MainLayoutProps {
  children: React.ReactNode
  title: string
  description: string
  keywords: string
}

const helmetContext = {}

const MainLayout = ({
  children,
  title,
  description,
  keywords,
}: MainLayoutProps) => {
  return (
    <HelmetProvider context={helmetContext}>
      <Helmet>
        <meta charSet="utf-8" />
        <meta name="description" content={description} />
        <meta name="keywords" content={keywords} />
        <link rel="icon" type="image/x-icon" href={favicon} />
        <title>{title}</title>
      </Helmet>
      <header></header>
      <main>{children}</main>
      <footer></footer>
    </HelmetProvider>
  )
}

MainLayout.defaultProps = {
  title: "Litestar Fullstack Application",
  description: "A fullstack reference application",
  keywords: "litestar",
}

export default MainLayout
