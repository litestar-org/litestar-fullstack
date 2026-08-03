import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { AvatarSection } from "@/components/profile/avatar-section"

// Mock the auth store, supporting the selector form the component uses.
const mockUser = vi.fn()
vi.mock("@/lib/auth", () => ({
  useAuthStore: (selector?: (state: { user: unknown }) => unknown) => {
    const state = { user: mockUser() }
    return selector ? selector(state) : state
  },
}))

// No real avatar image in jsdom, so the fallback initials always render.
vi.mock("@/hooks/use-auth", () => ({
  useAvatarSrc: () => undefined,
}))

const mockUploadMutate = vi.fn()
const mockRemoveMutate = vi.fn()
vi.mock("@/lib/api/hooks/profile", () => ({
  useUploadAvatar: () => ({ mutate: mockUploadMutate, isPending: false }),
  useDeleteAvatar: () => ({ mutate: mockRemoveMutate, isPending: false }),
}))

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

describe("AvatarSection", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("shows the upload action and initials when no avatar is set", async () => {
    mockUser.mockReturnValue({ name: "Ada Lovelace", username: "ada", avatarUrl: null })
    render(<AvatarSection />)

    expect(screen.getByRole("button", { name: /upload picture/i })).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /remove/i })).not.toBeInTheDocument()
    expect(await screen.findByText("AL")).toBeInTheDocument()
  })

  it("shows change and remove actions when an avatar is set", () => {
    mockUser.mockReturnValue({ name: "Ada Lovelace", username: "ada", avatarUrl: "/api/me/avatar" })
    render(<AvatarSection />)

    expect(screen.getByRole("button", { name: /change picture/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /remove/i })).toBeInTheDocument()
  })

  it("calls the delete mutation when remove is clicked", async () => {
    mockUser.mockReturnValue({ name: "Ada Lovelace", username: "ada", avatarUrl: "/api/me/avatar" })
    const user = userEvent.setup()
    render(<AvatarSection />)

    await user.click(screen.getByRole("button", { name: /remove/i }))

    expect(mockRemoveMutate).toHaveBeenCalledTimes(1)
  })
})
