export namespace API {
  export namespace AccountLogin {
    export namespace Http201 {
      export type ResponseBody = {
        access_token: string
        expires_in?: null | number
        refresh_token?: null | string
        token_type: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export type RequestBody = {
      password: string
      username: string
    }
  }

  export namespace AccountProfile {
    export namespace Http200 {
      export type ResponseBody = {
        avatarUrl?: null | string
        createdAt?: string
        email: string
        id?: string
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
        teams: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        updatedAt?: string
        verifiedAt?: string
      }
    }
  }

  export namespace AccountRegister {
    export namespace Http201 {
      export type ResponseBody = {
        avatarUrl?: null | string
        createdAt?: string
        email: string
        id?: string
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
        teams: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        updatedAt?: string
        verifiedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export type RequestBody = {
      email: string
      name?: null | string
      password: string
    }
  }

  export namespace CreateTag {
    export namespace Http201 {
      export type ResponseBody = {
        createdAt?: string
        description?: null | string
        id?: string
        name: string
        slug: string
        teams: {
          createdAt?: string
          description?: null | string
          id?: string
          invitations: {
            createdAt?: string
            email: string
            id?: string
            invitedByEmail: string
            invitedById?: null | string
            isAccepted?: boolean
            role?: "ADMIN" | "MEMBER"
            teamId: string
            updatedAt?: string
          }[]
          isActive?: boolean
          members: {
            createdAt?: string
            email: string
            id?: string
            isOwner?: boolean
            name: string
            role?: "ADMIN" | "MEMBER"
            teamId: string
            teamName: string
            updatedAt?: string
            userId: string
          }[]
          name: string
          pendingInvitations: {
            createdAt?: string
            email: string
            id?: string
            invitedByEmail: string
            invitedById?: null | string
            isAccepted?: boolean
            role?: "ADMIN" | "MEMBER"
            teamId: string
            updatedAt?: string
          }[]
          slug: string
          tags: {
            createdAt?: string
            description?: null | string
            id?: string
            name: string
            slug: string
            updatedAt?: string
          }[]
          updatedAt?: string
        }[]
        updatedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export type RequestBody = {
      description?: null | string
      name: string
      slug: string
    }
  }

  export namespace CreateTeam {
    export namespace Http201 {
      export type ResponseBody = {
        createdAt?: string
        description?: null | string
        id?: string
        isActive?: boolean
        members: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        name: string
        slug: string
        tags: {
          createdAt?: string
          description?: null | string
          id?: string
          name: string
          slug: string
          updatedAt?: string
        }[]
        updatedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export type RequestBody = {
      description?: null | string
      name: string
      tags?: string[]
    }
  }

  export namespace CreateUser {
    export namespace Http201 {
      export type ResponseBody = {
        avatarUrl?: null | string
        createdAt?: string
        email: string
        id?: string
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
        teams: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        updatedAt?: string
        verifiedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export type RequestBody = {
      email: string
      isActive?: boolean
      isSuperuser?: boolean
      isVerified?: boolean
      name?: null | string
      password: string
    }
  }

  export namespace DeleteTag {
    export namespace Http204 {
      export type ResponseBody = undefined
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      tag_id: string
    }
  }

  export namespace DeleteTeam {
    export namespace Http204 {
      export type ResponseBody = undefined
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      team_id: string
    }
  }

  export namespace DeleteUser {
    export namespace Http204 {
      export type ResponseBody = undefined
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      user_id: string
    }
  }

  export namespace GetTag {
    export namespace Http200 {
      export type ResponseBody = {
        createdAt?: string
        description?: null | string
        id?: string
        name: string
        slug: string
        teams: {
          createdAt?: string
          description?: null | string
          id?: string
          invitations: {
            createdAt?: string
            email: string
            id?: string
            invitedByEmail: string
            invitedById?: null | string
            isAccepted?: boolean
            role?: "ADMIN" | "MEMBER"
            teamId: string
            updatedAt?: string
          }[]
          isActive?: boolean
          members: {
            createdAt?: string
            email: string
            id?: string
            isOwner?: boolean
            name: string
            role?: "ADMIN" | "MEMBER"
            teamId: string
            teamName: string
            updatedAt?: string
            userId: string
          }[]
          name: string
          pendingInvitations: {
            createdAt?: string
            email: string
            id?: string
            invitedByEmail: string
            invitedById?: null | string
            isAccepted?: boolean
            role?: "ADMIN" | "MEMBER"
            teamId: string
            updatedAt?: string
          }[]
          slug: string
          tags: {
            createdAt?: string
            description?: null | string
            id?: string
            name: string
            slug: string
            updatedAt?: string
          }[]
          updatedAt?: string
        }[]
        updatedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      tag_id: string
    }
  }

  export namespace GetTeam {
    export namespace Http200 {
      export type ResponseBody = {
        createdAt?: string
        description?: null | string
        id?: string
        isActive?: boolean
        members: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        name: string
        slug: string
        tags: {
          createdAt?: string
          description?: null | string
          id?: string
          name: string
          slug: string
          updatedAt?: string
        }[]
        updatedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      team_id: string
    }
  }

  export namespace GetUser {
    export namespace Http200 {
      export type ResponseBody = {
        avatarUrl?: null | string
        createdAt?: string
        email: string
        id?: string
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
        teams: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        updatedAt?: string
        verifiedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      user_id: string
    }
  }

  export namespace ListTags {
    export namespace Http200 {
      export type ResponseBody = {
        createdAt?: string
        description?: null | string
        id?: string
        name: string
        slug: string
        teams: {
          createdAt?: string
          description?: null | string
          id?: string
          invitations: {
            createdAt?: string
            email: string
            id?: string
            invitedByEmail: string
            invitedById?: null | string
            isAccepted?: boolean
            role?: "ADMIN" | "MEMBER"
            teamId: string
            updatedAt?: string
          }[]
          isActive?: boolean
          members: {
            createdAt?: string
            email: string
            id?: string
            isOwner?: boolean
            name: string
            role?: "ADMIN" | "MEMBER"
            teamId: string
            teamName: string
            updatedAt?: string
            userId: string
          }[]
          name: string
          pendingInvitations: {
            createdAt?: string
            email: string
            id?: string
            invitedByEmail: string
            invitedById?: null | string
            isAccepted?: boolean
            role?: "ADMIN" | "MEMBER"
            teamId: string
            updatedAt?: string
          }[]
          slug: string
          tags: {
            createdAt?: string
            description?: null | string
            id?: string
            name: string
            slug: string
            updatedAt?: string
          }[]
          updatedAt?: string
        }[]
        updatedAt?: string
      }[]
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface QueryParameters {
      createdAfter?: null | string
      createdBefore?: null | string
      currentPage?: number
      ids?: null | string[]
      orderBy?: null | string
      pageSize?: number
      searchField?: null | string
      searchIgnoreCase?: boolean | null
      searchString?: null | string
      sortOrder?: "asc" | "desc" | null
      updatedAfter?: null | string
      updatedBefore?: null | string
    }
  }

  export namespace ListTeams {
    export namespace Http200 {
      export type ResponseBody = {
        createdAt?: string
        description?: null | string
        id?: string
        isActive?: boolean
        members: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        name: string
        slug: string
        tags: {
          createdAt?: string
          description?: null | string
          id?: string
          name: string
          slug: string
          updatedAt?: string
        }[]
        updatedAt?: string
      }[]
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface QueryParameters {
      createdAfter?: null | string
      createdBefore?: null | string
      currentPage?: number
      ids?: null | string[]
      orderBy?: null | string
      pageSize?: number
      searchField?: null | string
      searchIgnoreCase?: boolean | null
      searchString?: null | string
      sortOrder?: "asc" | "desc" | null
      updatedAfter?: null | string
      updatedBefore?: null | string
    }
  }

  export namespace ListUsers {
    export namespace Http200 {
      export type ResponseBody = {
        avatarUrl?: null | string
        createdAt?: string
        email: string
        id?: string
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
        teams: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        updatedAt?: string
        verifiedAt?: string
      }[]
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface QueryParameters {
      createdAfter?: null | string
      createdBefore?: null | string
      currentPage?: number
      ids?: null | string[]
      orderBy?: null | string
      pageSize?: number
      searchField?: null | string
      searchIgnoreCase?: boolean | null
      searchString?: null | string
      sortOrder?: "asc" | "desc" | null
      updatedAfter?: null | string
      updatedBefore?: null | string
    }
  }

  export namespace SystemHealth {
    export namespace Http200 {
      export type ResponseBody = {
        app?: string
        cache_status: "offline" | "online"
        database_status: "offline" | "online"
        version?: string
        worker_status: "offline" | "online"
      }
    }
  }

  export namespace UpdateTag {
    export namespace Http200 {
      export type ResponseBody = {
        createdAt?: string
        description?: null | string
        id?: string
        name: string
        slug: string
        teams: {
          createdAt?: string
          description?: null | string
          id?: string
          invitations: {
            createdAt?: string
            email: string
            id?: string
            invitedByEmail: string
            invitedById?: null | string
            isAccepted?: boolean
            role?: "ADMIN" | "MEMBER"
            teamId: string
            updatedAt?: string
          }[]
          isActive?: boolean
          members: {
            createdAt?: string
            email: string
            id?: string
            isOwner?: boolean
            name: string
            role?: "ADMIN" | "MEMBER"
            teamId: string
            teamName: string
            updatedAt?: string
            userId: string
          }[]
          name: string
          pendingInvitations: {
            createdAt?: string
            email: string
            id?: string
            invitedByEmail: string
            invitedById?: null | string
            isAccepted?: boolean
            role?: "ADMIN" | "MEMBER"
            teamId: string
            updatedAt?: string
          }[]
          slug: string
          tags: {
            createdAt?: string
            description?: null | string
            id?: string
            name: string
            slug: string
            updatedAt?: string
          }[]
          updatedAt?: string
        }[]
        updatedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      tag_id: string
    }

    export type RequestBody = {
      description: null | string
      name: string
      slug: string
    }
  }

  export namespace UpdateTeam {
    export namespace Http200 {
      export type ResponseBody = {
        createdAt?: string
        description?: null | string
        id?: string
        isActive?: boolean
        members: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        name: string
        slug: string
        tags: {
          createdAt?: string
          description?: null | string
          id?: string
          name: string
          slug: string
          updatedAt?: string
        }[]
        updatedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      team_id: string
    }

    export type RequestBody = {
      description: null | string
      name: null | string
      tags: null | string[]
    }
  }

  export namespace UpdateUser {
    export namespace Http200 {
      export type ResponseBody = {
        avatarUrl?: null | string
        createdAt?: string
        email: string
        id?: string
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
        teams: {
          createdAt?: string
          email: string
          id?: string
          isOwner?: boolean
          name: string
          role?: "ADMIN" | "MEMBER"
          teamId: string
          teamName: string
          updatedAt?: string
          userId: string
        }[]
        updatedAt?: string
        verifiedAt?: string
      }
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      user_id: string
    }

    export type RequestBody = {
      email: null | string
      isActive: boolean | null
      isSuperuser: boolean | null
      isVerified: boolean | null
      name: null | string
      password: null | string
    }
  }

  export namespace WorkerJobAbort {
    export namespace Http202 {
      export type ResponseBody = {}
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      job_id: string
      queue_id: string
    }
  }

  export namespace WorkerJobDetail {
    export namespace Http200 {
      export type ResponseBody = {}
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      job_id: string
      queue_id: string
    }
  }

  export namespace WorkerJobRetry {
    export namespace Http202 {
      export type ResponseBody = {}
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      job_id: string
      queue_id: string
    }
  }

  export namespace WorkerQueueDetail {
    export namespace Http200 {
      export type ResponseBody = {}
    }

    export namespace Http400 {
      export type ResponseBody = {
        detail: string
        extra?: Record<string, unknown> | null | unknown[]
        status_code: number
      }
    }

    export interface PathParameters {
      queue_id: string
    }
  }

  export namespace WorkerQueueList {
    export namespace Http200 {
      export type ResponseBody = {}
    }
  }
}
