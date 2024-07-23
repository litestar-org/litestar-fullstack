interface FlashMessages {
  [category: string]: string[]
}
export type CurrentTeam = { teamId: string; teamName: string }
export type AuthData = {
  isAuthenticated: boolean
  user?: AuthenticatedUserData
}
export type UserTeam = {
  email: string
  id: string
  userId: string
  isOwner?: boolean
  name: string
  role?: "ADMIN" | "MEMBER"
  teamId: string
  teamName: string
  createdAt?: string
  updatedAt?: string
}
export type AuthenticatedUserData = {
  email: string
  id: string
  isActive?: boolean
  isSuperuser?: boolean
  isVerified?: boolean
  joinedAt?: string
  loginCount?: number
  name?: null | string
  oauthAccounts: {
    accessToken: string
    accountEmail: string
    accountId: string
    createdAt?: string
    expiresAt?: null | number
    id?: string
    oauthName: string
    refreshToken?: null | string
    updatedAt?: string
    userEmail: string
    userId: string
    userName: string
  }[]
  roles: {
    assignedAt?: string
    createdAt?: string
    id?: string
    roleId: string
    roleName: string
    roleSlug: string
    updatedAt?: string
    userEmail: string
    userId: string
    userName: string
  }[]
  teams: UserTeam[]
  avatarUrl?: null | string
  verifiedAt?: string
  createdAt?: string
  updatedAt?: string
}
