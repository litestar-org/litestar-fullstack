interface FlashMessages {
  [category: string]: string[]
}

export type AuthData = {
  user: AuthenticatedUserData
}
export type AuthenticatedUserData = {
  id: number
  email: string
  name: string
  gravatar: string
  email_verified_at: string | null
}
