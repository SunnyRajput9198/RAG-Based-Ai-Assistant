'use client'

import { useEffect, useRef } from 'react'
import { ChatMessage } from '@/components/chat-message'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{
    videoId: number
    videoTitle: string
    timestamp: string
  }>
}

interface ChatInterfaceProps {
  messages: Message[]
  isLoading: boolean
}

export function ChatInterface({ messages, isLoading }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto flex flex-col">
      {messages.length === 0 ? (
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="text-center max-w-2xl">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-secondary/20 border border-primary/30 flex items-center justify-center mx-auto mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-bold">
                E
              </div>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground mb-2">
              Welcome to EduBot
            </h2>
            <p className="text-muted-foreground text-sm sm:text-base mb-6">
              Your personal AI teaching assistant. Ask questions about the course material and get instant answers with source citations from the video lessons.
            </p>
            <div className="space-y-3">
              <p className="text-xs font-semibold text-primary uppercase tracking-wide">
                Getting Started
              </p>
              <ul className="text-sm text-foreground/80 space-y-2">
                <li>✨ Ask specific questions about course topics</li>
                <li>📹 Get citations linking to exact video timestamps</li>
                <li>💡 Learn with AI-powered explanations</li>
              </ul>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-4 sm:p-6 lg:p-8 space-y-4 max-w-3xl mx-auto w-full">
          {messages.map((message, idx) => (
            <ChatMessage
              key={idx}
              role={message.role}
              content={message.content}
              sources={message.sources}
            />
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-card border border-border rounded-xl px-4 py-3 shadow-lg">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-xs font-bold">
                    AI
                  </div>
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" />
                    <div className="w-2 h-2 rounded-full bg-secondary animate-bounce delay-100" />
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce delay-200" />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  )
}
