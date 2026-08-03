import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { MIN_DIMENSION, validateAvatarFile } from "@/lib/avatar-validation"

function makeFile({ name = "avatar.png", type = "image/png", size = 1024 }: { name?: string; type?: string; size?: number } = {}): File {
  const file = new File([new Uint8Array(0)], name, { type })
  // Override size so we don't have to allocate multi-MB buffers in tests.
  Object.defineProperty(file, "size", { value: size, configurable: true })
  return file
}

function mockBitmap(width: number, height: number) {
  globalThis.createImageBitmap = vi.fn().mockResolvedValue({ width, height, close: vi.fn() } as unknown as ImageBitmap)
}

describe("validateAvatarFile", () => {
  beforeEach(() => {
    // Valid dimensions by default; individual tests override as needed.
    mockBitmap(512, 512)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("accepts a valid PNG within all limits", async () => {
    expect(await validateAvatarFile(makeFile())).toBeNull()
  })

  it("rejects an unsupported type such as GIF", async () => {
    const result = await validateAvatarFile(makeFile({ name: "a.gif", type: "image/gif" }))
    expect(result).toMatch(/JPEG, PNG, or WebP/)
  })

  it("rejects when the file extension does not match the type", async () => {
    const result = await validateAvatarFile(makeFile({ name: "a.gif", type: "image/png" }))
    expect(result).toMatch(/extension/)
  })

  it("rejects an empty file", async () => {
    const result = await validateAvatarFile(makeFile({ size: 0 }))
    expect(result).toMatch(/empty/)
  })

  it("rejects a file larger than 2 MB", async () => {
    const result = await validateAvatarFile(makeFile({ size: 2 * 1024 * 1024 + 1 }))
    expect(result).toMatch(/2 MB/)
  })

  it("rejects an image below the minimum dimension", async () => {
    mockBitmap(MIN_DIMENSION - 1, MIN_DIMENSION)
    const result = await validateAvatarFile(makeFile())
    expect(result).toMatch(/at least/)
  })

  it("rejects bytes that cannot be decoded as an image", async () => {
    globalThis.createImageBitmap = vi.fn().mockRejectedValue(new Error("decode failed"))
    const result = await validateAvatarFile(makeFile())
    expect(result).toMatch(/Could not read/)
  })
})
