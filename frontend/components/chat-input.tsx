'use client'

import { useState, useEffect } from 'react'
import { Send, Sparkles, CornerDownLeft, Mic } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useRef } from 'react'
import { cn } from '@/lib/utils'
import { SuggestedQuestions } from './suggested-questions'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  suggestedQuestions?: string[]  // 🆕 ADDED
  onSuggestedQuestionClick?: (question: string) => void  // 🆕 ADDED
  isLoading?: boolean  // 🆕 ADDED
}
declare global {
  interface Window {
    SpeechRecognition: any
    webkitSpeechRecognition: any
  }
}


export function ChatInput({
  onSendMessage,
  suggestedQuestions = [],
  onSuggestedQuestionClick,
  isLoading = false
}: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [isListening, setIsListening] = useState(false)

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input)
      setInput('')
      if (textareaRef.current) textareaRef.current.style.height = 'auto'
    }
  }
  // docs for voice input
  // https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition/start
  const handleVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.onstart = () => setIsListening(true)
    recognition.onend = () => setIsListening(false)
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      setInput(transcript)
    }
    recognition.start()
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
<div className="border-t border-border/40 bg-background/80 backdrop-blur-xl transition-all duration-300">
      <div className="px-4 pb-6 pt-4 max-w-4xl mx-auto w-full space-y-4">

        {/* Suggested Questions: Positioned slightly above input */}
        {suggestedQuestions.length > 0 && onSuggestedQuestionClick && (
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1">
            <Sparkles className="h-3 w-3 text-primary shrink-0 animate-pulse" />
            <SuggestedQuestions
              questions={suggestedQuestions}
              onQuestionClick={onSuggestedQuestionClick}
              isLoading={isLoading}
            />
          </div>
        )}

        {/* Input Area Wrapper */}
        <div className="relative group">
          {/* Subtle Glow Effect on Focus */}
          <div className="absolute -inset-1 bg-linear-to-r from-primary/20 to-secondary/20 rounded-[22px] blur opacity-0 group-focus-within:opacity-100 transition duration-500" />

          <div className={cn(
            "relative flex flex-col bg-card border border-border/60 rounded-2xl shadow-2xl transition-all duration-200 overflow-hidden",
            isLoading ? "opacity-80" : "group-hover:border-border group-focus-within:border-primary/40 group-focus-within:shadow-primary/5"
          )}>

            <textarea
              ref={textareaRef}
              id="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask a question about the course materials..."
              disabled={isLoading}
              rows={1}
              className="w-full bg-transparent text-[15px] px-4 pt-4 pb-2 outline-none text-foreground placeholder:text-muted-foreground/60 resize-none min-h-14 max-h-40"
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement
                target.style.height = 'auto'
                target.style.height = `${target.scrollHeight}px`
              }}
            />

            <div className="flex items-center justify-between px-3 pb-3">
              {/* Keyboard Shortcut Hints */}
              <div className="flex items-center gap-3">
                <TooltipProvider delayDuration={0}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center gap-1.5 text-[10px] font-medium text-muted-foreground/60 cursor-help hover:text-muted-foreground transition-colors">
                        <kbd className="px-1.5 py-0.5 rounded border border-border bg-muted/50 font-sans">Enter</kbd>
                        <span>to send</span>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="bg-popover text-[11px] border-border/40">
                      Use <span className="font-bold text-primary">Shift + Enter</span> for a new line
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                {input.length > 0 && (
                  <span className={cn(
                    "text-[10px] font-mono mr-2",
                    input.length > 450 ? "text-destructive" : "text-muted-foreground/40"
                  )}>
                    {input.length}/500
                  </span>
                )}

                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  size="sm"
                  className={cn(
                    "h-8 px-4 rounded-xl transition-all duration-300",
                    "bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200",
                    "shadow-[0_0_20px_-5px_rgba(0,0,0,0.2)]"
                  )}
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 border-2 border-current/30 border-t-current rounded-full animate-spin" />
                      <span className="text-xs font-semibold">Thinking</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold">Send</span>
                      <CornerDownLeft className="h-3 w-3 opacity-50" />
                    </div>
                  )}
                </Button>
                <Button
                  onClick={handleVoiceInput}
                  disabled={isLoading}
                  size="sm"
                  variant="ghost"
                  className={cn(
                    "h-8 w-8 rounded-xl",
                    isListening && "text-red-500 animate-pulse"
                  )}
                >
                  <Mic className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Brand Footer */}
        <div className="flex flex-col items-center gap-1">
          <p className="text-[11px] text-muted-foreground/50 flex items-center gap-2 font-medium">
            EduBot v1.0 • Powered by RAG & Video-LLM
          </p>
        </div>
      </div>
    </div>
  )
}