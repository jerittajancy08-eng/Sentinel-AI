import type { StreamEvent } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Streams a Sentinel AI investigation via Server-Sent Events.
 * Calls `onEvent` for each event as agents complete and the
 * Judge Agent produces the final report.
 */
export async function streamInvestigation(
  text: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/investigate/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, content_type: "text" }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Investigation request failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;

      const payload = trimmed.slice(5).trim();
      if (payload === "[DONE]") return;

      try {
        const parsed: StreamEvent = JSON.parse(payload);
        onEvent(parsed);
      } catch {
        // ignore malformed chunks
      }
    }
  }
}

/**
 * Non-streaming investigation — returns the full report at once.
 */
export async function investigate(text: string) {
  const response = await fetch(`${API_BASE}/api/investigate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, content_type: "text" }),
  });

  if (!response.ok) {
    throw new Error(`Investigation request failed: ${response.status}`);
  }

  return response.json();
}
