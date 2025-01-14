import favicon from "@/assets/favicon.png"
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
      <meta charSet="utf-8" />
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <link rel="icon" type="image/x-icon" href={favicon} />
      <title>{title}</title>
      <header></header>
      <main>{children}</main>
      <footer></footer>
    </>
  )
}

MainLayout.defaultProps = {
  title: "Litestar Fullstack Application",
  description: "A fullstack reference application",
  keywords: "litestar",
}

export default MainLayout
