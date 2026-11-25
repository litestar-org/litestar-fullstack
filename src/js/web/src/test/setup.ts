import "@testing-library/jest-dom/vitest"
import { cleanup } from "@testing-library/react"
import { afterEach } from "vitest"

function createMemoryStorage(): Storage {
  const store = new Map<string, string>()
  return {
    get length() {
      return store.size
    },
    clear() {
      store.clear()
    },
    getItem(key: string) {
      return store.has(key) ? (store.get(key) ?? null) : null
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null
    },
    removeItem(key: string) {
      store.delete(key)
    },
    setItem(key: string, value: string) {
      store.set(key, String(value))
    },
  }
}

if (typeof globalThis.localStorage?.clear !== "function") {
  Object.defineProperty(globalThis, "localStorage", { value: createMemoryStorage(), configurable: true })
}
if (typeof globalThis.sessionStorage?.clear !== "function") {
  Object.defineProperty(globalThis, "sessionStorage", { value: createMemoryStorage(), configurable: true })
}

// jsdom has no layout engine, so media queries never match.
if (typeof window.matchMedia !== "function") {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: (query: string): MediaQueryList => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }),
  })
}

// jsdom does not implement scrolling; the router restores scroll position on navigation.
window.scrollTo = () => {}

afterEach(() => {
  cleanup()
})
