import * as React from "react"

const MOBILE_BREAKPOINT = 768

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined)

  React.useEffect(() => {
    const mediaQueryList = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const handleChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    mediaQueryList.addEventListener("change", handleChange)
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    return () => mediaQueryList.removeEventListener("change", handleChange)
  }, [])

  return !!isMobile
}
