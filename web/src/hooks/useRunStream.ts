import { useEffect, useReducer, useRef } from 'react'
import { subscribeToStream } from '../lib/sse'
import { initialRunViewState, runEventReducer, type RunViewState } from '../lib/runReducer'
import type { RunEvent } from '../lib/types'

/** Subscribes to a run's SSE stream and exposes live RunViewState, with
 * cleanup on unmount/runId change and basic reconnect-safety (closes on
 * run_finished so EventSource's native auto-reconnect never replays a
 * completed run). */
export function useRunStream(runId: string | null): { state: RunViewState; connectionError: boolean } {
  const [state, dispatch] = useReducer(runEventReducer, initialRunViewState)
  const errorRef = useRef(false)
  const [, forceRender] = useReducer((c: number) => c + 1, 0)

  useEffect(() => {
    if (!runId) return
    errorRef.current = false
    const cleanup = subscribeToStream<RunEvent>(
      `/api/runs/${runId}/events`,
      (event) => dispatch(event),
      () => {
        /* stream closed normally on run_finished */
      },
      () => {
        errorRef.current = true
        forceRender()
      },
    )
    return cleanup
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId])

  return { state, connectionError: errorRef.current }
}
