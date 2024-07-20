interface FlashMessages {
  [category: string]: string[]
}

export type AuthData = {
  is_authenticated: boolean
  user?: AuthenticatedUserData
}
export type AuthenticatedUserData = {
  id: number
  email: string
  name: string
  gravatar: string
  email_verified_at: string | null
}
