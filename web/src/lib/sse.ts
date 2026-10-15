/**
 * Thin wrapper around EventSource for the run/benchmark event streams.
 * The server sends every event as a plain `data: {...}` frame (the event
 * type lives inside the JSON payload's "event" key), so a bare
 * EventSource onmessage handler is all that's needed -- no custom parsing.
 */
export function subscribeToStream<T>(
  url: string,
  onEvent: (event: T) => void,
  onDone: () => void,
  onError?: (err: unknown) => void,
): () => void {
  const source = new EventSource(url)

  source.onmessage = (ev) => {
    try {
      const parsed = JSON.parse(ev.data) as T & { event?: string }
      onEvent(parsed as T)
      if (
        (parsed as { event?: string }).event === 'run_finished' ||
        (parsed as { event?: string }).event === 'benchmark_finished'
      ) {
        source.close()
        onDone()
      }
    } catch (err) {
      onError?.(err)
    }
  }

  source.onerror = (err) => {
    onError?.(err)
  }

  return () => source.close()
}
