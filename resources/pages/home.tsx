import { Head } from "@inertiajs/react"
import { AppLayout } from "@/layouts/app-layout"
import { Header } from "@/components/header"
import { Container } from "@/components/container"
import { cn } from "@/lib/utils"
import { Icons } from "@/components/icons"

import { BeakerIcon } from "lucide-react"
export default function Home() {
  return (
    <>
      <Head title="Welcome to Litestar" />
      <Header title="Inertia Typescript" />
      <Container>
        <div className="overflow-hidden rounded-lg border">
          <div>
            <div className="p-4 sm:p-20">
              <div>
                <svg
                  viewBox="0 52 410 250"
                  xmlns="http://www.w3.org/2000/svg"
                  className="block h-12 w-auto fill-current text-red-500"
                >
                  <defs>
                    <clipPath id="9eb7762d41">
                      <path
                        d="M 15.933594 105 L 328 105 L 328 259 L 15.933594 259 Z M 15.933594 105 "
                        clip-rule="nonzero"
                      />
                    </clipPath>
                    <clipPath id="183d3cc178">
                      <path
                        d="M 142 78.769531 L 359.433594 78.769531 L 359.433594 296.269531 L 142 296.269531 Z M 142 78.769531 "
                        clip-rule="nonzero"
                      />
                    </clipPath>
                  </defs>
                  <g clip-path="url(#9eb7762d41)">
                    <path
                      fill="#edb641"
                      d="M 147.625 240.3125 C 161.5 233.984375 173.554688 227.011719 183.425781 220.550781 C 202.304688 208.203125 226.4375 185.242188 227.761719 183.410156 L 218.917969 177.503906 L 211.257812 172.386719 L 235.503906 171.441406 L 243.296875 171.136719 L 245.414062 163.640625 L 252.007812 140.304688 L 260.402344 163.054688 L 263.097656 170.363281 L 270.890625 170.058594 L 295.136719 169.113281 L 276.078125 184.117188 L 269.953125 188.9375 L 272.652344 196.25 L 281.046875 218.996094 L 260.871094 205.523438 L 254.390625 201.195312 L 248.265625 206.015625 L 229.207031 221.023438 L 232.480469 209.425781 L 235.796875 197.691406 L 236.207031 196.234375 C 213.003906 213.585938 180.546875 230.304688 161.140625 236.488281 C 156.6875 237.90625 152.183594 239.179688 147.625 240.3125 Z M 101.992188 258.078125 C 136.382812 256.734375 177.355469 248 217.675781 222.363281 L 209.90625 249.867188 L 254.910156 214.4375 L 302.539062 246.246094 L 282.71875 192.539062 L 327.71875 157.109375 L 270.46875 159.34375 L 250.648438 105.636719 L 235.085938 160.726562 L 177.835938 162.964844 L 210.980469 185.097656 C 189.164062 204.921875 134.445312 247.195312 61.957031 250.03125 C 47.300781 250.601562 31.914062 249.558594 15.933594 246.394531 C 15.933594 246.394531 52.011719 260.035156 101.992188 258.078125 "
                      fill-opacity="1"
                      fill-rule="nonzero"
                    />
                  </g>
                  <g clip-path="url(#183d3cc178)">
                    <path
                      fill="#edb641"
                      d="M 250.789062 78.96875 C 190.78125 78.96875 142.140625 127.570312 142.140625 187.519531 C 142.140625 198.875 143.886719 209.816406 147.121094 220.101562 C 151.847656 217.75 156.363281 215.316406 160.660156 212.84375 C 158.394531 204.789062 157.183594 196.296875 157.183594 187.519531 C 157.183594 135.871094 199.089844 93.996094 250.789062 93.996094 C 302.484375 93.996094 344.390625 135.871094 344.390625 187.519531 C 344.390625 239.171875 302.484375 281.042969 250.789062 281.042969 C 222.75 281.042969 197.597656 268.722656 180.441406 249.210938 C 175.453125 251.152344 170.402344 252.917969 165.289062 254.511719 C 185.183594 279.816406 216.082031 296.070312 250.789062 296.070312 C 310.792969 296.070312 359.433594 247.472656 359.433594 187.519531 C 359.433594 127.570312 310.792969 78.96875 250.789062 78.96875 "
                      fill-opacity="1"
                      fill-rule="nonzero"
                    />
                  </g>
                  <path
                    fill="#edb641"
                    d="M 92.292969 173.023438 L 98.289062 191.460938 L 117.691406 191.460938 L 101.992188 202.855469 L 107.988281 221.292969 L 92.292969 209.898438 L 76.59375 221.292969 L 82.589844 202.855469 L 66.894531 191.460938 L 86.296875 191.460938 L 92.292969 173.023438 "
                    fill-opacity="1"
                    fill-rule="nonzero"
                  />
                  <path
                    fill="#edb641"
                    d="M 120.214844 112.25 L 125.390625 128.167969 L 142.140625 128.167969 L 128.589844 138 L 133.765625 153.917969 L 120.214844 144.082031 L 106.664062 153.917969 L 111.839844 138 L 98.289062 128.167969 L 115.039062 128.167969 L 120.214844 112.25 "
                    fill-opacity="1"
                    fill-rule="nonzero"
                  />
                  <path
                    fill="#edb641"
                    d="M 34.695312 209.136719 L 37.71875 218.421875 L 47.492188 218.421875 L 39.585938 224.160156 L 42.605469 233.449219 L 34.695312 227.707031 L 26.792969 233.449219 L 29.8125 224.160156 L 21.90625 218.421875 L 31.679688 218.421875 L 34.695312 209.136719 "
                    fill-opacity="1"
                    fill-rule="nonzero"
                  />
                </svg>
              </div>
              <div className="max-w-2xl">
                <div className="mt-6 text-xl sm:mt-8 sm:text-2xl">
                  Litestar application with Inertia and React Typescript!
                </div>
                <div className="mt-4 text-muted-foreground sm:mt-6 sm:text-lg">
                  This is a Litestar application with Inertia and React
                  Typescript. It is a work in progress. If you have any
                  questions or suggestions, please feel free to contact me.
                </div>
              </div>

              <div className="mt-16 grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border bg-secondary/20 p-8">
                  <a
                    href="https://github.com/litestar-org/litestar-fullstack"
                    className="flex items-center gap-x-2 font-semibold text-primary"
                    target="_blank"
                  >
                    <Icons.gitHub className="size-8 stroke-1" />
                    Litestar
                  </a>
                  <p className="mt-5 text-muted-foreground">
                    This project is developed by{" "}
                    <a
                      href="https://litestar.dev"
                      target="_blank"
                      className="text-foreground font-semibold"
                    >
                      Litestar
                    </a>
                    , if you want to contribute to this project, please visit
                    the{" "}
                    <a
                      href="https://github.com/litestar-org/litestar-fullstack"
                      target="_blank"
                      className="text-foreground font-semibold"
                    >
                      Github Repository
                    </a>
                    .
                  </p>
                </div>
                <div className="rounded-xl border bg-secondary/20 p-8">
                  <a
                    href="https://github.com/litestar-org/litestar-fullstack"
                    className="flex items-center gap-x-2 font-semibold text-primary"
                    target="_blank"
                  >
                    <Icons.inertia className="size-8 stroke-1" />
                    Inertia
                  </a>
                  <p className="mt-5 text-muted-foreground">
                    Create modern single-page React, Vue, and Svelte apps using
                    classic server-side routing. Works with any backend.
                  </p>
                </div>

                <div className="rounded-xl border bg-secondary/20 p-8">
                  <a
                    href="https://paranoid.irsyad.co"
                    className="flex items-center gap-x-2 font-semibold text-primary"
                    target="_blank"
                  >
                    <BeakerIcon className="size-8" />
                    Advanced Alchemy
                  </a>
                  <p className="mt-5 text-muted-foreground">
                    A carefully crafted, thoroughly tested, optimized companion
                    library for SQLAlchemy
                  </p>
                </div>
                <div className="rounded-xl border bg-secondary/20 p-8">
                  <a
                    href="https://irsyad.co/s"
                    className="flex items-center gap-x-2 font-semibold text-primary"
                    target="_blank"
                  >
                    <Icons.react className="size-8" />
                    React Template
                  </a>
                  <p className="mt-5 text-muted-foreground">
                    Explore the next.js templates from web apps to design
                    systems, all here.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </>
  )
}

function ParsintaLogo() {
  return (
    <svg
      className="w-8"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width={32} height={32} rx={8} fill="#2563EB" />
      <path
        d="M22.6706 23.1516C22.9947 23.4991 23.5421 23.5202 23.8622 23.1691C25.0074 21.9133 25.838 20.3979 26.279 18.748C26.7944 16.8202 26.7573 14.7864 26.1719 12.8788C25.5865 10.9712 24.4765 9.26657 22.9687 7.95967C21.4608 6.65277 19.6157 5.79623 17.6443 5.48786C15.6728 5.1795 13.6544 5.43173 11.8194 6.21575C9.98449 6.99978 8.40699 8.284 7.26707 9.92178C6.12715 11.5596 5.47076 13.4849 5.37284 15.4779C5.28902 17.1837 5.61723 18.8803 6.32419 20.4259C6.52183 20.858 7.04948 21.005 7.46419 20.7731V20.7731C7.8789 20.5412 8.0229 20.0183 7.83202 19.5832C7.27872 18.3219 7.02343 16.9458 7.0914 15.5623C7.17349 13.8916 7.72373 12.2776 8.67931 10.9047C9.63489 9.53179 10.9573 8.45525 12.4955 7.79801C14.0337 7.14077 15.7257 6.92933 17.3784 7.18783C19.031 7.44633 20.5777 8.16435 21.8417 9.25991C23.1058 10.3555 24.0363 11.7844 24.527 13.3835C25.0177 14.9827 25.0488 16.6876 24.6168 18.3036C24.2591 19.6417 23.5957 20.8742 22.6837 21.9062C22.3691 22.2623 22.3466 22.8042 22.6706 23.1516V23.1516Z"
        fill="white"
        fillOpacity="0.3"
      />
      <path
        d="M15.9999 6.22514C15.9999 5.74735 15.6119 5.35636 15.1357 5.39517C13.3359 5.54182 11.5979 6.14471 10.0886 7.15318C8.33889 8.32232 6.97513 9.98406 6.16982 11.9283C5.3645 13.8725 5.15379 16.0118 5.56434 18.0758C5.97489 20.1397 6.98825 22.0356 8.47628 23.5236C9.96431 25.0117 11.8602 26.025 13.9241 26.4356C15.9881 26.8461 18.1274 26.6354 20.0716 25.8301C22.0158 25.0248 23.6776 23.661 24.8467 21.9113C25.8552 20.402 26.4581 18.664 26.6047 16.8642C26.6435 16.388 26.2526 16 25.7748 16V16C25.297 16 24.914 16.3883 24.8677 16.8638C24.7257 18.3209 24.2264 19.7254 23.4081 20.95C22.4291 22.4152 21.0375 23.5572 19.4095 24.2315C17.7815 24.9059 15.99 25.0823 14.2617 24.7386C12.5334 24.3948 10.9458 23.5462 9.69975 22.3002C8.4537 21.0541 7.60513 19.4665 7.26135 17.7382C6.91756 16.0099 7.094 14.2184 7.76836 12.5904C8.44272 10.9624 9.5847 9.57085 11.0499 8.59183C12.2745 7.77355 13.679 7.27416 15.1361 7.13223C15.6116 7.08591 15.9999 6.70294 15.9999 6.22514V6.22514Z"
        fill="white"
      />
      <path
        d="M19.2341 15.122C19.9007 15.5069 19.9007 16.4692 19.2341 16.8541L15.1148 19.2323C14.4482 19.6172 13.6148 19.1361 13.6148 18.3663V13.6098C13.6148 12.84 14.4482 12.3589 15.1148 12.7438L19.2341 15.122Z"
        fill="white"
      />
    </svg>
  )
}

function KarteilLogo({ className }: { className?: string }) {
  return (
    <svg
      className={cn(className, "text-primary")}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 155 155"
    >
      <rect
        x=".8"
        y="41.6"
        width={120}
        height={120}
        rx="29.8"
        transform="rotate(-20 .8 41.6)"
        fill="currentColor"
      />
      <path
        d="M35.6 92.2c-.6 0-.8 0-1-.2-.2-.2-.2-.4-.2-1V54.6c0-.5 0-.8.2-1l1-.1H42l1 .1.1 1v20c0 1.6 0 2.3.4 2.5.4 0 .8-.6 1.7-1.8l6-9.3.4-.5h7.5c1 0 1.4 0 1.5.3.2.3 0 .6-.6 1.4l-7.4 11-.3.6c0 .1 0 .3.3.6l7.8 11c.6.8.9 1.2.7 1.5-.2.3-.6.3-1.6.3h-7.4l-.5-.1-.4-.4-6-9.1c-.9-1.3-1.3-1.9-1.7-1.8-.4.1-.4.9-.4 2.4V91l-.1 1c-.2.2-.5.2-1 .2h-6.4Z"
        fill="currentColor"
        className="text-primary-foreground"
      />
      <path
        d="M72.4 64.2a10.5 10.5 0 0 1 7.7 3c.4.2.6 0 .7-.3v-1.6c.1-.2.3-.4.5-.4h7l1 .1v26.5h-8a.6.6 0 0 1-.2-.2l-.1-.6v-1.5l-.6-.3a6 6 0 0 0-1.4 1l-1.4 1a12.6 12.6 0 0 1-14.7-2.7 14 14 0 0 1-3.8-10c0-4 1.2-7.3 3.8-10 2.5-2.6 5.7-4 9.5-4ZM74.2 85c1.9 0 3.4-.6 4.7-1.9a6.7 6.7 0 0 0 1.8-4.9c0-2-.6-3.6-1.8-4.8a6.2 6.2 0 0 0-4.7-2 6 6 0 0 0-4.6 2 6.8 6.8 0 0 0-1.8 4.8c0 2 .6 3.6 1.8 4.9a6 6 0 0 0 4.6 2Z"
        fill="currentColor"
        className="text-primary-foreground"
      />
      <rect
        x="103.4"
        y="38.1"
        width="8.6"
        height="66.9"
        rx=".6"
        transform="rotate(12 103.4 38.1)"
        fill="#3B82F6"
      />
      <rect
        x="109.6"
        y="61.6"
        width="8.6"
        height="42.9"
        rx=".6"
        transform="rotate(12 109.6 61.6)"
        fill="#3B82F6"
      />
    </svg>
  )
}
Home.layout = (page: any) => <AppLayout children={page} />