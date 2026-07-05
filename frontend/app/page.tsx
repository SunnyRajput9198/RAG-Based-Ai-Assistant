'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { Navbar } from '@/components/navbar'
import { VideoSidebar } from '@/components/video-sidebar'
import { ChatInterface } from '@/components/chat-interface'
import { ChatInput } from '@/components/chat-input'
import { Button } from '@/components/ui/button'
import { Trash2 } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'

const API = 'http://localhost:8000'
const MAX_RETRIES = 3
const BASE_RETRY_DELAY_MS = 1000  // doubles each attempt: 1s, 2s, 4s

interface Source {
  videoId: string
  videoTitle: string
  timestamp: string
  timestamp_seconds?: number
  similarity: number
  text_preview: string
  source_type?: 'video' | 'pdf'
  video_url?: string | null
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  suggestedQuestions?: string[]
}

// ── Robust SSE parser ─────────────────────────────────────────────────────────
/**
 * Parses a raw SSE stream from a ReadableStreamDefaultReader.
 *
 * Why not just split on '\n'?
 * A single `reader.read()` chunk may contain a partial multi-byte character
 * (e.g. a UTF-8 emoji split across two reads) or a partial JSON payload sliced
 * at the chunk boundary. Naively calling buffer.split('\n').pop() can silently
 * drop the tail — or worse, try to JSON.parse an incomplete string.
 *
 * This parser:
 * 1. Uses TextDecoder with `stream: true` so multi-byte chars are never split.
 * 2. Accumulates a byte-safe buffer string.
 * 3. Only slices complete lines (terminated by \n).
 * 4. Leaves any incomplete trailing line in the buffer for the next read.
 */
async function* parseSseStream(
  reader: ReadableStreamDefaultReader<Uint8Array>
): AsyncGenerator<Record<string, unknown>> {
  const decoder = new TextDecoder('utf-8', { fatal: false })
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // `stream: true` preserves partial multi-byte sequences across reads
      buffer += decoder.decode(value, { stream: true })

      // Process all complete lines — split only on \n, keep the incomplete tail
      let newlineIndex: number
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex).trimEnd()  // strip \r too
        buffer = buffer.slice(newlineIndex + 1)

        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6)
        if (!raw || raw === '[DONE]') continue

        try {
          yield JSON.parse(raw) as Record<string, unknown>
        } catch {
          // Malformed JSON from a partial chunk — ignore and continue
        }
      }
    }

    // Flush any remaining bytes in the decoder (handles final multi-byte seq)
    buffer += decoder.decode()
  } finally {
    reader.releaseLock()
  }
}

// ── Exponential backoff fetch with retry ──────────────────────────────────────
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  maxRetries: number,
  baseDelay: number
): Promise<Response> {
  let lastError: unknown

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url, options)
      // Only retry on network/server errors, not on 4xx (client errors)
      if (res.ok || (res.status >= 400 && res.status < 500)) {
        return res
      }
      // 5xx — treat as retryable
      lastError = new Error(`HTTP ${res.status}`)
    } catch (err) {
      // Network failure (no response at all)
      lastError = err
      // Don't retry on AbortError — the user intentionally cancelled
      if (err instanceof Error && err.name === 'AbortError') throw err
    }

    if (attempt < maxRetries) {
      const delay = baseDelay * Math.pow(2, attempt)
      console.warn(`[SSE] Attempt ${attempt + 1} failed. Retrying in ${delay}ms…`)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw lastError
}

// ── Page component ────────────────────────────────────────────────────────────

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  }, [])

  const handleSendMessage = useCallback(async (message: string) => {
    if (isLoading) return

    setMessages(prev => [
      ...prev,
      { role: 'user', content: message },
      { role: 'assistant', content: '' },
    ])
    setIsLoading(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const res = await fetchWithRetry(
        `${API}/chat/stream`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message,
            VideoId: selectedVideoId,
            session_id: sessionId || null,
          }),
          signal: controller.signal,
        },
        MAX_RETRIES,
        BASE_RETRY_DELAY_MS
      )

      if (!res.ok) {
        const errText = await res.text().catch(() => `HTTP ${res.status}`)
        throw new Error(errText)
      }

      if (!res.body) throw new Error('Response has no body')

      // Stream the SSE events using the robust parser
      for await (const event of parseSseStream(res.body.getReader())) {
        const type = event.type as string

        if (type === 'token') {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: updated[updated.length - 1].content + (event.content as string),
            }
            return updated
          })
        } else if (type === 'done') {
          if (event.session_id) setSessionId(event.session_id as string)
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              sources: (event.sources as Source[]) ?? [],
              suggestedQuestions: (event.suggested_questions as string[]) ?? [],
            }
            return updated
          })
        } else if (type === 'error') {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1].content =
              (event.content as string) || 'Something went wrong.'
            return updated
          })
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        // User intentionally cancelled — leave the partial message as-is
        return
      }

      const errMsg = err instanceof Error ? err.message : 'Unknown error'
      console.error('[SSE] Stream failed after retries:', errMsg)

      setMessages(prev => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        // Only overwrite if we haven't received any tokens yet
        if (!last.content) {
          last.content = `Connection failed after ${MAX_RETRIES} retries. Please try again.`
        }
        return updated
      })
    } finally {
      setIsLoading(false)
      abortRef.current = null
    }
  }, [selectedVideoId, sessionId, isLoading])

  const handleSuggestedQuestion = useCallback((question: string) => {
    handleSendMessage(question)
  }, [handleSendMessage])

  const handleClearChat = async () => {
    abortRef.current?.abort()
    setMessages([])
    const newSession = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    try {
      await fetch(`${API}/clear-history?session_id=${encodeURIComponent(sessionId)}`, {
        method: 'POST',
      })
    } catch { /* non-critical */ }
    setSessionId(newSession)
  }

  const messageCount = messages.filter(m => m.role === 'user').length

  return (
    <div className="h-screen overflow-hidden">
      <Navbar />

      <div className="flex" style={{ height: 'calc(100vh - 64px)', marginTop: '64px' }}>

        <VideoSidebar
          selectedVideoId={selectedVideoId}
          onSelectVideo={setSelectedVideoId}
        />

        <div className="flex-1 flex flex-col bg-background relative" style={{ overflow: 'hidden' }}>

          {messages.length > 0 && (
            <div className="absolute top-3 right-4 z-10 flex items-center gap-2">
              <div className="text-xs text-muted-foreground bg-card/80 backdrop-blur-sm px-3 py-1.5 rounded-full border border-border shadow-sm">
                {messageCount} {messageCount === 1 ? 'question' : 'questions'} asked
              </div>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-2 bg-card/80 backdrop-blur-sm hover:bg-destructive/10 hover:text-destructive hover:border-destructive/50"
                  >
                    <Trash2 className="h-4 w-4" />
                    Clear Chat
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Clear conversation?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will delete all messages and conversation memory. This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleClearChat}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      Clear Chat
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          )}

          <div className="flex-1 min-h-0" style={{ overflow: 'clip' }}>
            <ChatInterface
              messages={messages}
              isLoading={isLoading}
              onSuggestedQuestionClick={handleSuggestedQuestion}
            />
          </div>

          <div className="shrink-0 border-t border-border/40">
            <ChatInput
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
