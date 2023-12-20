import { Helmet } from "react-helmet"

interface MainLayoutProps {
  children: React.ReactNode
  title: string
  description: string
  keywords: string
}

const MainLayout = ({
  children,
  title,
  description,
  keywords,
}: MainLayoutProps) => {
  return (
    <>
      <Helmet>
        <meta charSet="utf-8" />
        <meta name="description" content={description} />
        <meta name="keywords" content={keywords} />
        <title>{title}</title>
      </Helmet>
      <header></header>
      <main>{children}</main>
      <footer></footer>
    </>
  )
}

MainLayout.defaultProps = {
  title: "Litestar Application",
  description: "Gemini, Vertex... and Databases?",
  keywords: "database, dma",
}

export default MainLayout
