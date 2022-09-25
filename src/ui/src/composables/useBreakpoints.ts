import { breakpointsTailwind, useBreakpoints } from "@vueuse/core"

const breakpoints = useBreakpoints(breakpointsTailwind)

export const smAndLarger = breakpoints.greater("sm")
export const smAndSmaller = breakpoints.smaller("sm")
export const mdAndLarger = breakpoints.greater("md")
export const mdAndSmaller = breakpoints.smaller("md")
export const lgAndLarger = breakpoints.greater("lg")
export const lgAndSmaller = breakpoints.smaller("lg")
