import { act, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"
import { QueueActivityMonitor } from "@/components/queues/queue-activity-monitor"

class FakeWebSocket extends EventTarget {
  static instances: FakeWebSocket[] = []
  static readonly CONNECTING = 0
  static readonly OPEN = 1
  static readonly CLOSING = 2
  static readonly CLOSED = 3

  readonly url: string
  readyState = FakeWebSocket.CONNECTING
  closed = false

  constructor(url: string | URL) {
    super()
    this.url = String(url)
    FakeWebSocket.instances.push(this)
  }

  emitOpen() {
    this.readyState = FakeWebSocket.OPEN
    this.dispatchEvent(new Event("open"))
  }

  emitMessage(payload: unknown) {
    this.dispatchEvent(new MessageEvent("message", { data: JSON.stringify(payload) }))
  }

  emitClose(code = 1000) {
    this.readyState = FakeWebSocket.CLOSED
    const event = new Event("close")
    Object.defineProperty(event, "code", { value: code })
    this.dispatchEvent(event)
  }

  send = vi.fn()

  close() {
    this.closed = true
    this.readyState = FakeWebSocket.CLOSED
  }
}

describe("QueueActivityMonitor", () => {
  afterEach(() => {
    FakeWebSocket.instances = []
  })

  it("connects to /api/queues/events without double prefixing, renders events, handles gaps, and disposes on unmount", async () => {
    const onTaskEvent = vi.fn()
    const { unmount } = render(<QueueActivityMonitor basePath="" onTaskEvent={onTaskEvent} WebSocketCtor={FakeWebSocket as unknown as typeof WebSocket} />)

    expect(FakeWebSocket.instances).toHaveLength(1)
    const socket = FakeWebSocket.instances[0]
    expect(new URL(socket.url).pathname).toBe("/api/queues/events")

    act(() => {
      socket.emitOpen()
    })
    expect(screen.getByText("Connected")).toBeInTheDocument()

    act(() => {
      socket.emitMessage({
        taskId: "task-101",
        taskName: "send_verification_email",
        queue: "emails",
        status: "running",
        progress: 1,
        total: 2,
        message: "Sending email",
        timestamp: "2026-11-24T20:00:00Z",
        sequence: 1,
      })
    })

    expect(screen.getByText("send_verification_email")).toBeInTheDocument()
    expect(screen.getByText("emails")).toBeInTheDocument()
    expect(screen.getByText("Progress: 1 / 2")).toBeInTheDocument()
    expect(screen.getByText("Sending email")).toBeInTheDocument()
    expect(onTaskEvent).toHaveBeenCalledTimes(1)

    act(() => {
      socket.emitMessage({
        taskId: "task-102",
        taskName: "generate_report",
        queue: "emails",
        status: "completed",
        progress: 2,
        total: 2,
        message: null,
        timestamp: "2026-11-24T20:00:05Z",
        sequence: 4,
      })
    })

    expect(screen.getByText(/detected 2 missed event\(s\)/i)).toBeInTheDocument()

    unmount()
    expect(socket.closed).toBe(true)
  })

  it("suppresses reconnect and displays an authorization notice on close code 4003", async () => {
    render(<QueueActivityMonitor basePath="" WebSocketCtor={FakeWebSocket as unknown as typeof WebSocket} />)

    const socket = FakeWebSocket.instances[0]
    act(() => {
      socket.emitClose(4003)
    })

    expect(screen.getByText("Unauthorized")).toBeInTheDocument()
    expect(screen.getByRole("alert")).toHaveTextContent(/authorization required/i)
  })

  it("supports pausing and clearing displayed events", async () => {
    const user = userEvent.setup()
    render(<QueueActivityMonitor basePath="" WebSocketCtor={FakeWebSocket as unknown as typeof WebSocket} />)

    const socket = FakeWebSocket.instances[0]
    act(() => {
      socket.emitOpen()
      socket.emitMessage({
        taskId: "task-1",
        taskName: "first_task",
        queue: "default",
        status: "completed",
        timestamp: "2026-11-24T20:00:00Z",
      })
    })
    expect(screen.getByText("first_task")).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /pause/i }))
    act(() => {
      socket.emitMessage({
        taskId: "task-2",
        taskName: "hidden_while_paused",
        queue: "default",
        status: "running",
        timestamp: "2026-11-24T20:00:01Z",
      })
    })
    expect(screen.queryByText("hidden_while_paused")).not.toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /clear/i }))
    expect(screen.queryByText("first_task")).not.toBeInTheDocument()
  })
})
