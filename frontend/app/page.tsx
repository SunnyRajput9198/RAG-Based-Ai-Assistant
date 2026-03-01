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

// Source interface
interface Source {
  videoId: string
  videoTitle: string
  timestamp: string
  timestamp_seconds?: number  // 🆕 For clickable links
  similarity: number
  text_preview: string
  source_type?: 'video' | 'pdf'
  video_url?: string | null  // 🆕 YouTube URL
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
  const [sessionId, setSessionId] = useState<string>('')  // 🆕 Session tracking

  // 🆕 Generate session ID on mount
  useEffect(() => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    setSessionId(newSessionId)
    console.log('🧠 New session created:', newSessionId)
  }, [])

  const handleSendMessage = useCallback(async (message: string) => {
    setMessages(prev => [...prev, { role: 'user', content: message }])
    setIsLoading(true)

    // Add placeholder for assistant response
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message, 
          VideoId: selectedVideoId,
          session_id: sessionId  // 🆕 Send session ID
        }),
      })

      const data = await res.json()

      // Update the last assistant message with content AND sources
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: data.content,
          sources: data.sources  // Includes video_url and timestamp_seconds
        }
        return updated
      })

    } catch (error) {
      console.error('Error sending message:', error)
      // Update last message with error
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
    // 🆕 Clear chat on frontend AND backend
    setMessages([])
    
    // Clear backend conversation history
    try {
      await fetch("http://localhost:8000/clear-history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sessionId)
      })
      console.log('🧹 Conversation history cleared')
    } catch (error) {
      console.error('Failed to clear backend history:', error)
    }
    
    // Generate new session ID for fresh start
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    setSessionId(newSessionId)
    console.log('🆕 New session started:', newSessionId)
  }

  const messageCount = messages.filter(m => m.role === 'user').length

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* NAVBAR - Fixed height */}
      <Navbar />

      {/* MAIN CONTENT AREA - Takes remaining space */}
      <div className="flex flex-1 pt-16 overflow-hidden">
        {/* VIDEO SIDEBAR - Fixed width, scrollable */}
        <VideoSidebar
          selectedVideoId={selectedVideoId}
          onSelectVideo={setSelectedVideoId}
        />

        {/* CHAT AREA - Flex column, constrained */}
        <div className="flex-1 flex flex-col overflow-hidden bg-background min-h-0 relative">
          {/* Clear Chat Button - Only show when messages exist */}
          {messages.length > 0 && (
            <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
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

          {/* Chat messages - Scrollable, takes available space */}
          <div className="flex-1 overflow-y-auto min-h-0">
            <ChatInterface messages={messages} />
          </div>

          {/* Input area - Fixed at bottom, never scrolls away */}
          <div className="flex-shrink-0">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
          </div>
        </div>
      </div>
    </div>
  )
}