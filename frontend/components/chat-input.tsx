'use client'

import { useState, useEffect } from 'react'
import { Send, Sparkles, Command } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

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
  const [showShortcuts, setShowShortcuts] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Show shortcuts with Cmd/Ctrl + /
      if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault()
        setShowShortcuts(!showShortcuts)
      }
      // Focus input with Cmd/Ctrl + K
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        document.getElementById('chat-input')?.focus()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [showShortcuts])

  const handleSend = () => {
    if (input.trim() && !isLoading) {
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
    if (!isLoading) {
      onSendMessage(question)
    }
  }

  const charCount = input.length

  return (
    <div className="border-t border-border bg-gradient-to-b from-background to-card/30 backdrop-blur-sm">
      <div className="px-4 sm:px-6 lg:px-8 py-4 max-w-4xl mx-auto w-full">
        {/* Suggested Questions */}
        <div className="mb-3 flex flex-wrap gap-2 items-center">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
                  onClick={() => setShowShortcuts(!showShortcuts)}
                >
                  <Command className="h-3 w-3 mr-1" />
                  Shortcuts
                </Button>
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">
                <div className="space-y-1">
                  <p><kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">⌘/Ctrl + K</kbd> Focus input</p>
                  <p><kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">Enter</kbd> Send message</p>
                  <p><kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">Shift + Enter</kbd> New line</p>
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {SUGGESTED_QUESTIONS.map((question, idx) => (
            <Badge
              key={idx}
              variant="outline"
              className="cursor-pointer px-3 py-1.5 bg-card border-border hover:bg-primary/10 hover:border-primary/50 hover:shadow-sm transition-all text-foreground text-xs font-normal group"
              onClick={() => handleSuggestedQuestion(question)}
            >
              <Sparkles className="h-3 w-3 mr-1.5 text-primary group-hover:rotate-12 transition-transform" />
              {question}
            </Badge>
          ))}
        </div>

        {/* Input Area */}
        <div className="relative">
          <div
            className={`flex gap-3 bg-card border-2 rounded-2xl p-3 shadow-lg transition-all ${
              isLoading
                ? 'border-muted cursor-not-allowed opacity-60'
                : 'border-border hover:border-primary/30 focus-within:border-primary/50 focus-within:ring-4 focus-within:ring-primary/10'
            }`}
          >
            <textarea
              id="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask anything about the course..."
              disabled={isLoading}
              rows={1}
              className="flex-1 bg-transparent text-sm outline-none text-foreground placeholder-muted-foreground disabled:cursor-not-allowed resize-none max-h-32"
              maxLength={500}
              style={{
                minHeight: '24px',
                height: 'auto',
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement
                target.style.height = 'auto'
                target.style.height = target.scrollHeight + 'px'
              }}
            />

            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              size="sm"
              className="bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed gap-2 shadow-md hover:shadow-lg transition-all self-end"
            >
              {isLoading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span className="hidden sm:inline">Thinking...</span>
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  <span className="hidden sm:inline">Send</span>
                </>
              )}
            </Button>
          </div>

          {/* Character Counter */}
          {charCount > 0 && (
            <p
              className={`absolute -bottom-5 right-0 text-xs transition-colors ${
                charCount > 450 ? 'text-destructive' : 'text-muted-foreground'
              }`}
            >
              {charCount}/500
            </p>
          )}
        </div>

        <p className="text-xs text-muted-foreground mt-6 text-center flex items-center justify-center gap-2">
          <span className="w-1 h-1 rounded-full bg-primary" />
          EduBot provides AI-generated answers with video source citations
          <span className="w-1 h-1 rounded-full bg-primary" />
        </p>
      </div>
    </div>
  )
}