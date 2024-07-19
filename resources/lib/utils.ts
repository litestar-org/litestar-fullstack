import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { ErrorBag, Errors } from "@inertiajs/core"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function strLimit(value: string, limit: number, end = "...") {
  return value.length > limit ? value.substring(0, limit) + end : value
}

export function getFirstWord(value: string) {
  return value.split(" ")[0]
}

export function getServerSideErrors(errors: Errors & ErrorBag = {}) {
  const err = Object.entries(errors).reduce((acc, [key, value]) => {
    return {
      ...acc,
      [key]: {
        message: value,
      },
    }
  }, {})
  return err
}
