'use client'

import { useState, useCallback, useEffect } from 'react'
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
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [selectedVideoId, setSelectedVideoId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')

  useEffect(() => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    setSessionId(newSessionId)
  }, [])

  const handleSendMessage = useCallback(async (message: string) => {
    setMessages(prev => [...prev, { role: 'user', content: message }])
    setIsLoading(true)
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])
    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, VideoId: selectedVideoId, session_id: sessionId || null }),
      })
      const data = await res.json()
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { role: 'assistant', content: data.content, sources: data.sources }
        return updated
      })
    } catch (error) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1].content = "Sorry, I encountered an error. Please try again."
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }, [selectedVideoId, sessionId])

  const handleClearChat = async () => {
    setMessages([])
    try {
      await fetch("http://localhost:8000/clear-history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sessionId)
      })
    } catch (error) {
      console.error('Failed to clear backend history:', error)
    }
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  }

  const messageCount = messages.filter(m => m.role === 'user').length

  return (
    <div>
      <Navbar />

      {/* Full remaining height below fixed navbar */}
      <div className="flex" style={{ height: 'calc(100vh - 64px)', marginTop: '64px' }}>

        {/* Sidebar */}
        <VideoSidebar selectedVideoId={selectedVideoId} onSelectVideo={setSelectedVideoId} />

        {/* Chat column — flex column, overflow hidden so children control scroll */}
        <div className="flex-1 flex flex-col bg-background relative" style={{ overflow: 'hidden' }}>

          {/* Clear chat button */}
          {messages.length > 0 && (
            <div className="absolute top-3 right-4 z-10 flex items-center gap-2">
              <div className="text-xs text-muted-foreground bg-card/80 backdrop-blur-sm px-3 py-1.5 rounded-full border border-border shadow-sm">
                {messageCount} {messageCount === 1 ? 'question' : 'questions'} asked
              </div>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-2 bg-card/80 backdrop-blur-sm hover:bg-destructive/10 hover:text-destructive hover:border-destructive/50">
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
                    <AlertDialogAction onClick={handleClearChat} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                      Clear Chat
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          )}

          {/* Messages — flex-1 + min-h-0, NO overflow-y here, ChatInterface scrolls itself */}
          <div className="flex-1 min-h-0">
            <ChatInterface messages={messages} isLoading={isLoading} />
          </div>

          {/* Input — always pinned at bottom */}
          <div className="shrink-0 border-t border-border/40">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
          </div>

        </div>
      </div>
    </div>
  )
}