'use client'

import { useState } from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isLoading?: boolean
}

const SUGGESTED_QUESTIONS = [
  'What is Flexbox?',
  'Explain CSS Grid',
  'How to use media queries?',
]

export function ChatInput({ onSendMessage, isLoading = false }: ChatInputProps) {
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input)
      setInput('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestedQuestion = (question: string) => {
    onSendMessage(question)
    setInput('')
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8 pb-6 max-w-3xl mx-auto w-full">
      {/* Suggested Questions */}
      <div className="mb-4 flex flex-wrap gap-2">
        {SUGGESTED_QUESTIONS.map((question, idx) => (
          <Badge
            key={idx}
            variant="outline"
            className="cursor-pointer px-3 py-1.5 bg-card border-border hover:bg-muted hover:border-primary/50 transition-all text-foreground text-xs"
            onClick={() => handleSuggestedQuestion(question)}
          >
            {question}
          </Badge>
        ))}
      </div>

      {/* Input Area */}
      <div className="flex gap-2 bg-card border border-border rounded-xl p-3 shadow-lg hover:border-primary/50 transition-colors focus-within:border-primary/80 focus-within:ring-2 focus-within:ring-primary/20">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask anything about the course..."
          className="flex-1 bg-transparent text-sm outline-none text-foreground placeholder-muted-foreground"
        />
        <Button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          size="sm"
          className="bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed gap-2"
        >
          <Send className="h-4 w-4" />
          <span className="hidden sm:inline">Send</span>
        </Button>
      </div>

      <p className="text-xs text-muted-foreground mt-3 text-center">
        EduBot can help you understand course concepts. Ask specific questions to get detailed answers with source citations.
      </p>
    </div>
  )
}
