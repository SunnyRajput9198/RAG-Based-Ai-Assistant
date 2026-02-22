'use client'

import { useState, useCallback } from 'react'
import { Navbar } from '@/components/navbar'
import { VideoSidebar } from '@/components/video-sidebar'
import { ChatInterface } from '@/components/chat-interface'
import { ChatInput } from '@/components/chat-input'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{
    videoId: number
    videoTitle: string
    timestamp: string
  }>
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [selectedVideoId, setSelectedVideoId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)

const handleSendMessage = useCallback(async (message: string) => {
  setMessages((prev) => [...prev, { role: 'user', content: message }])
  setIsLoading(true)

  const res = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  })
  const data = await res.json()

  setMessages((prev) => [...prev, { role: 'assistant', content: data.content, sources: data.sources }])
  setIsLoading(false)
}, [])
  return (
    <div className="h-screen bg-background text-foreground overflow-hidden flex flex-col">
      <Navbar selectedVideoId={selectedVideoId} onSelectVideo={setSelectedVideoId} />
      
      <div className="flex flex-1 mt-16 overflow-hidden">
        <VideoSidebar selectedVideoId={selectedVideoId} onSelectVideo={setSelectedVideoId} />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatInterface messages={messages} isLoading={isLoading} />
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  )
}
