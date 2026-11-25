import { createTypedChannels, type StreamGap } from "litestar-vite-plugin/helpers"
import { AlertTriangle, Pause, Play, Radio, Trash2, Wifi, WifiOff } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CHANNEL_METADATA, type ChannelKey, type QueueTaskEventPayload, type RealtimeChannels } from "@/lib/generated/channels"

const MAX_EVENTS = 100
const QUEUE_EVENTS_CHANNEL: ChannelKey = "api__queues__events"

type QueueEventChannelMap = {
  [K in ChannelKey]: Omit<RealtimeChannels[K], "receive" | "send"> & {
    receive: QueueTaskEventPayload
    send: never
  }
}

export interface QueueActivityMonitorProps {
  basePath?: string
  onTaskEvent?: (event: QueueTaskEventPayload) => void
  WebSocketCtor?: typeof WebSocket
  EventSourceCtor?: typeof EventSource
}

function extractEventSequence(frame: QueueTaskEventPayload): { stream: string; value: number } | undefined {
  const candidate = frame as QueueTaskEventPayload & { seq?: unknown; sequence?: unknown }
  const raw = [candidate.sequence, candidate.seq].find((value) => typeof value === "number")
  if (typeof raw !== "number" || !Number.isFinite(raw)) {
    return undefined
  }
  return { stream: frame.queue || "default", value: raw }
}

function statusBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  const normalized = status.toLowerCase()
  if (normalized === "completed" || normalized === "succeeded") return "default"
  if (normalized === "failed" || normalized === "cancelled" || normalized === "canceled") return "destructive"
  if (normalized === "running" || normalized === "in_progress") return "secondary"
  return "outline"
}

interface MonitorEventEntry {
  id: number
  payload: QueueTaskEventPayload
}

function ConnectionBadge({ authDenied, healthy }: Readonly<{ authDenied: boolean; healthy: boolean }>) {
  if (authDenied) {
    return (
      <Badge variant="destructive" className="gap-1">
        <WifiOff className="h-3 w-3" />
        Unauthorized
      </Badge>
    )
  }
  if (healthy) {
    return (
      <Badge variant="default" className="gap-1">
        <Wifi className="h-3 w-3" />
        Connected
      </Badge>
    )
  }
  return (
    <Badge variant="secondary" className="gap-1">
      <WifiOff className="h-3 w-3" />
      Reconnecting
    </Badge>
  )
}

export function QueueActivityMonitor({ basePath = "", onTaskEvent, WebSocketCtor, EventSourceCtor }: Readonly<QueueActivityMonitorProps>) {
  const [events, setEvents] = useState<MonitorEventEntry[]>([])
  const [healthy, setHealthy] = useState(false)
  const [paused, setPaused] = useState(false)
  const [authDenied, setAuthDenied] = useState(false)
  const [gapWarning, setGapWarning] = useState<StreamGap | null>(null)
  const nextEventIdRef = useRef(0)

  const pausedRef = useRef(paused)
  pausedRef.current = paused

  const onTaskEventRef = useRef(onTaskEvent)
  onTaskEventRef.current = onTaskEvent

  useEffect(() => {
    setAuthDenied(false)
    const channels = createTypedChannels<QueueEventChannelMap>({
      basePath,
      metadata: CHANNEL_METADATA,
    })

    const stream = channels.stream(QUEUE_EVENTS_CHANNEL, {
      WebSocketCtor,
      EventSourceCtor,
      onEvent: (event) => {
        if (!pausedRef.current) {
          nextEventIdRef.current += 1
          const entry: MonitorEventEntry = { id: nextEventIdRef.current, payload: event }
          setEvents((prev) => [entry, ...prev].slice(0, MAX_EVENTS))
        }
        onTaskEventRef.current?.(event)
      },
      onHealthChange: (isHealthy) => {
        setHealthy(isHealthy)
        if (isHealthy) {
          setAuthDenied(false)
        }
      },
      getSequence: extractEventSequence,
      onGap: (gap) => {
        setGapWarning(gap)
      },
      shouldReconnect: (closeCode) => {
        if (closeCode === 4003 || closeCode === 403) {
          setAuthDenied(true)
          setHealthy(false)
          return false
        }
        return true
      },
    })

    stream.connect()
    return () => {
      stream.dispose()
    }
  }, [basePath, WebSocketCtor, EventSourceCtor])

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Radio className="h-4 w-4" />
            Live Queue Activity
          </CardTitle>
          <CardDescription>Real-time task lifecycle events streamed from {CHANNEL_METADATA[QUEUE_EVENTS_CHANNEL].address}.</CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ConnectionBadge authDenied={authDenied} healthy={healthy} />
          <Button type="button" variant="outline" size="sm" onClick={() => setPaused((prev) => !prev)}>
            {paused ? <Play className="mr-1.5 h-3.5 w-3.5" /> : <Pause className="mr-1.5 h-3.5 w-3.5" />}
            {paused ? "Resume" : "Pause"}
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => setEvents([])} disabled={events.length === 0}>
            <Trash2 className="mr-1.5 h-3.5 w-3.5" />
            Clear
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {authDenied && (
          <div role="alert" className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>Authorization required to stream queue events. Sign in with an authorized account and reload.</span>
          </div>
        )}
        {gapWarning && (
          <div className="flex items-center justify-between gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-700 dark:text-amber-300">
            <output className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>
                Detected {gapWarning.missing} missed event(s) on stream {gapWarning.stream} ({gapWarning.from} → {gapWarning.to}). Refresh the task list for latest state.
              </span>
            </output>
            <Button type="button" variant="ghost" size="sm" onClick={() => setGapWarning(null)}>
              Dismiss
            </Button>
          </div>
        )}
        {events.length === 0 ? (
          <p className="text-sm text-muted-foreground">{paused ? "Event stream paused. Resume to display incoming task events." : "Waiting for queue task events…"}</p>
        ) : (
          <div className="max-h-80 space-y-2 overflow-y-auto pr-1">
            {events.map(({ id, payload: event }) => {
              const hasProgress = typeof event.progress === "number" && typeof event.total === "number" && event.total > 0
              return (
                <div key={id} className="flex flex-col gap-1 rounded-lg border border-border/60 bg-muted/30 px-3 py-2 text-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{event.taskName}</span>
                      <Badge variant="outline" className="text-xs">
                        {event.queue}
                      </Badge>
                      <Badge variant={statusBadgeVariant(event.status)} className="text-xs capitalize">
                        {event.status}
                      </Badge>
                    </div>
                    <span className="text-xs text-muted-foreground">{new Date(event.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                    <span className="font-mono">{event.taskId}</span>
                    {hasProgress && (
                      <span>
                        Progress: {event.progress} / {event.total}
                      </span>
                    )}
                  </div>
                  {event.message && <p className="text-xs text-muted-foreground">{event.message}</p>}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
