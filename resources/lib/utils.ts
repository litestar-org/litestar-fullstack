import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { ErrorBag, Errors } from "@inertiajs/core"
import md5 from "md5"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function strLimit(value: string, limit: number, end = "...") {
  return value.length > limit ? value.substring(0, limit) + end : value
}

export function getFirstWord(value: string) {
  return value.split(" ")[0]
}

export const getInitials = (name: string) => {
  name = name.trim()

  if (name.length <= 3) return name

  return name
    .split(/\s+/)
    .map((w) => [...w][0])
    .slice(0, 3)
    .join("")
}

export const getGravatarUrl = (email: string, size?: number) => {
  email = email.trim()
  if (!email) return ""
  if (!size) {
    size = 50
  }
  const emailMd5 = md5(email)
  return `https://www.gravatar.com/avatar/${emailMd5}?s=${String(
    Math.max(size, 250)
  )}&d=identicon`
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
