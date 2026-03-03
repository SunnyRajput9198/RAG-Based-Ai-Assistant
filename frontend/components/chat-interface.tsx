'use client'

import { useEffect, useRef } from 'react'
import { ChatMessage } from '@/components/chat-message'
import { MessageSquare, Zap, ShieldCheck, Search } from 'lucide-react'

interface Source {
  videoId: string
  videoTitle: string
  timestamp: string
  similarity: number
  text_preview: string
  source_type?: 'video' | 'pdf'
  video_url?: string | null
  timestamp_seconds?: number
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  suggestedQuestions?: string[]
}

interface ChatInterfaceProps {
  messages: Message[]
  onSuggestedQuestionClick?: (question: string) => void
  isLoading?: boolean
}

export function ChatInterface({
  messages,
  onSuggestedQuestionClick,
  isLoading = false
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (messages.length === 0) {
    return (
      <div className="h-full overflow-y-auto">
        <div className="h-full flex items-center justify-center p-6 lg:p-12">
          <div className="max-w-2xl w-full">
            <div className="text-center mb-10 space-y-4">
              <div className="relative inline-block">
                <div className="absolute -inset-2 bg-linear-to-r from-primary to-secondary rounded-2xl blur-xl opacity-20 animate-pulse" />
                <div className="relative w-20 h-20 mx-auto rounded-3xl bg-zinc-950 border border-white/10 flex items-center justify-center shadow-2xl">
                  <MessageSquare className="h-10 w-10 text-primary" />
                </div>
              </div>
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tight text-foreground">
                  EduBot <span className="text-primary">Intelligence</span>
                </h2>
                <p className="text-muted-foreground text-sm max-w-sm mx-auto leading-relaxed">
                  Analyze course videos and documents in seconds with our advanced RAG engine.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <FeatureCard icon={<Search className="w-5 h-5 text-blue-500" />} title="Deep Search" desc="Search through transcripts and PDF content simultaneously." />
              <FeatureCard icon={<Zap className="w-5 h-5 text-yellow-500" />} title="Instant Clips" desc="Get direct links to the exact second a topic is mentioned." />
              <FeatureCard icon={<ShieldCheck className="w-5 h-5 text-green-500" />} title="Verified" desc="Every claim is backed by a cited source from your data." />
            </div>
            <p className="mt-8 text-center text-[11px] text-muted-foreground/60 font-medium uppercase tracking-[0.2em]">
              Ready when you are. Just type below.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // KEY: h-full + overflow-y-auto is the ONE scroll container. No nesting.
  return (
    <div className="h-full overflow-y-auto scroll-smooth">
      <div className="max-w-3xl mx-auto px-4 pt-6 pb-4 sm:px-6 space-y-4">
        {messages.map((message, idx) => (
          <ChatMessage
            key={idx}
            role={message.role}
            content={message.content}
            sources={message.sources}
            suggestedQuestions={message.suggestedQuestions}
            onSuggestedQuestionClick={onSuggestedQuestionClick}
            isLoading={isLoading && idx === messages.length - 1}
          />
        ))}
        {isLoading && messages[messages.length - 1].role === 'user' && (
          <div className="animate-pulse flex space-x-4 pl-2 py-4">
            <div className="rounded-lg bg-muted h-8 w-8" />
            <div className="flex-1 space-y-4 py-1">
              <div className="h-2 bg-muted rounded w-3/4" />
              <div className="h-2 bg-muted rounded w-1/2" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} className="h-4" />
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="p-5 rounded-2xl bg-card border border-border/50 hover:border-primary/20 hover:shadow-lg transition-all group">
      <div className="mb-3 p-2 w-fit rounded-lg bg-muted/50 group-hover:bg-primary/5 transition-colors">{icon}</div>
      <h3 className="text-sm font-semibold text-foreground mb-1">{title}</h3>
      <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
    </div>
  )
}