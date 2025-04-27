import { createClient } from "@hey-api/client-axios";
import type { paths } from "@/openapi";
import type { RequestOptions } from "@hey-api/client-axios";

const client = createClient({
  baseUrl: import.meta.env.VITE_API_URL || "http://localhost:8000",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
  },
});

type LoginRequest = paths["/api/access/login"]["post"]["requestBody"]["content"]["application/x-www-form-urlencoded"];
type TeamCreateRequest = paths["/api/teams"]["post"]["requestBody"]["content"]["application/json"];
type TeamUpdateRequest = paths["/api/teams/{team_id}"]["patch"]["requestBody"]["content"]["application/json"];
type TeamMemberAddRequest = paths["/api/teams/{team_id}/members"]["post"]["requestBody"]["content"]["application/json"];

type ApiOptions<T> = Omit<RequestOptions<false, T>, "method">;

export const api = {
  auth: {
    login: (data: LoginRequest) =>
      client.post<LoginRequest>("/api/access/login", { data } as ApiOptions<LoginRequest>),
    logout: () => client.post("/api/access/logout", {} as ApiOptions<void>),
    me: () => client.get("/api/me", {} as ApiOptions<void>),
  },
  teams: {
    list: () => client.get("/api/teams", {} as ApiOptions<void>),
    create: (data: TeamCreateRequest) =>
      client.post("/api/teams", { data } as ApiOptions<TeamCreateRequest>),
    get: (teamId: string) => client.get(`/api/teams/${teamId}`, {} as ApiOptions<void>),
    update: (teamId: string, data: TeamUpdateRequest) =>
      client.patch(`/api/teams/${teamId}`, { data } as ApiOptions<TeamUpdateRequest>),
    delete: (teamId: string) => client.delete(`/api/teams/${teamId}`, {} as ApiOptions<void>),
    members: {
      list: (teamId: string) => client.get(`/api/teams/${teamId}/members`, {} as ApiOptions<void>),
      add: (teamId: string, data: TeamMemberAddRequest) =>
        client.post(`/api/teams/${teamId}/members`, { data } as ApiOptions<TeamMemberAddRequest>),
      remove: (teamId: string, memberId: string) =>
        client.delete(`/api/teams/${teamId}/members/${memberId}`, {} as ApiOptions<void>),
    },
  },
  admin: {
    users: {
      list: () => client.get("/api/admin/users", {} as ApiOptions<void>),
      toggleSuperuser: (userId: string) =>
        client.post(`/api/admin/users/${userId}/toggle-superuser`, {} as ApiOptions<void>),
    },
  },
};

export type ApiError = paths["/api/access/login"]["post"]["responses"]["400"]["content"]["application/json"];
export type User = paths["/api/me"]["get"]["responses"]["200"]["content"]["application/json"];
export type Team = paths["/api/teams/{team_id}"]["get"]["responses"]["200"]["content"]["application/json"];
export type TeamMember = paths["/api/teams/{team_id}/members"]["get"]["responses"]["200"]["content"]["application/json"][0];
