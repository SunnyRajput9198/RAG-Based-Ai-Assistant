'use client'

import { useEffect, useRef } from 'react'
import { ChatMessage } from '@/components/chat-message'
import { MessageSquare, Sparkles } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: {
    VideoId: number
    videoTitle: string
    timestamp: string
  }[]
}

interface ChatInterfaceProps {
  messages: Message[]
}

export function ChatInterface({ messages }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Smooth scroll to bottom when new messages arrive
    if (messagesEndRef.current && containerRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [messages])

  if (messages.length === 0) {
    // EMPTY STATE - Centered content
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center max-w-md space-y-6">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg">
            <MessageSquare className="h-8 w-8 text-white" />
          </div>
          
          <div className="space-y-2">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text text-transparent">
              Welcome to EduBot! 👋
            </h2>
            <p className="text-muted-foreground text-sm">
              Your AI-powered teaching assistant for the course. Ask me anything about the videos, and I'll provide detailed answers with source citations.
            </p>
          </div>

          <div className="space-y-3 text-left bg-card/50 border border-border rounded-xl p-4">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground">Ask specific questions</p>
                <p className="text-xs text-muted-foreground">Example: "What is Flexbox and how does it work?"</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-secondary flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground">Filter by video</p>
                <p className="text-xs text-muted-foreground">Select a video from the sidebar to get context-specific answers</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground">Get source citations</p>
                <p className="text-xs text-muted-foreground">Every answer includes timestamps from relevant videos</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // MESSAGES VIEW - Scrollable content
  return (
    <div ref={containerRef} className="h-full">
      <div className="p-4 sm:p-6 lg:p-8 space-y-4 max-w-4xl mx-auto">
        {messages.map((message, idx) => (
          <ChatMessage
            key={idx}
            role={message.role}
            content={message.content}
            sources={message.sources}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}