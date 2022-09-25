import {
 
  Token,
  User,
  Users,
} from "@/api/client"
import {
  ANONYMOUS_AUTH,
  ANONYMOUS_USER,
  Auth,
 
  DEFAULT_USERS,
 
} from "@/api/types"
import Storage from "@/plugins/storage"
import jwtDecode, { JwtPayload } from "jwt-decode"
import { acceptHMRUpdate, defineStore } from "pinia"
import { ref } from "vue"

export const authStorage = new Storage<{ currentUser: User; auth: Auth }>("auth")

export const useAppStore = defineStore("app", () => {
  const currentUser = ref<User>(authStorage.get()?.currentUser || ANONYMOUS_USER)
  const auth = ref<Auth>(authStorage.get()?.auth || ANONYMOUS_AUTH)
 
  const sidebarOpen = ref(false)
  const darkMode = ref(false)
 
  const users = ref<Users>(DEFAULT_USERS)
  const selectedUser = ref<User>(ANONYMOUS_USER)
 

  function setAuth(tokenData?: Token) {
    if (tokenData === undefined || tokenData === null) {
      authStorage.remove()
      auth.value = ANONYMOUS_AUTH
      currentUser.value = ANONYMOUS_USER
    } else {
      const accessPayload = jwtDecode<JwtPayload>(tokenData.access_token || "")
      const refreshPayload = jwtDecode<JwtPayload>(tokenData.refresh_token || "")
      const authData = {
        userId: accessPayload.sub || "",
        accessToken: tokenData.access_token,
        refreshToken: tokenData.refresh_token || "",
        tokenType: tokenData.token_type,
        authenticatedAt: new Date(),
        accessTokenValidUntil: accessPayload.exp ? new Date(accessPayload.exp * 1000) : null,
        refreshTokenValidUntil: refreshPayload.exp ? new Date(refreshPayload.exp * 1000) : null,
      }
      authStorage.set({
        currentUser: tokenData.user,
        auth: authData,
      })
      currentUser.value = tokenData.user
      auth.value = authData
    }
  }
  function setCurrentUser(values: User) {
    currentUser.value = values
    authStorage.set({
      currentUser: currentUser.value,
      auth: auth.value,
    })
  }
  return {
    currentUser,
    auth,
 
    sidebarOpen,
    darkMode,
 
    users,
    selectedUser,
 
    setAuth,
    setCurrentUser,
  }
})

if (import.meta.hot) import.meta.hot.accept(acceptHMRUpdate(useAppStore, import.meta.hot))
