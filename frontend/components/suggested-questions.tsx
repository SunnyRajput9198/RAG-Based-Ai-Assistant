'use client'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Sparkles } from 'lucide-react'

interface SuggestedQuestionsProps {
  questions: string[]
  onQuestionClick: (question: string) => void
  isLoading?: boolean
}

export function SuggestedQuestions({ 
  questions, 
  onQuestionClick, 
  isLoading = false 
}: SuggestedQuestionsProps) {
  if (!questions || questions.length === 0) {
    return null
  }

  return (
    <div className="pl-11 mt-3 animate-in fade-in duration-500">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          You might also want to know
        </p>
      </div>

      <div className="space-y-2">
        {questions.map((question, idx) => (
          <Card
            key={idx}
            className="p-3 bg-linear-to-r from-primary/5 to-secondary/5 border border-primary/20 hover:border-primary/40 hover:from-primary/10 hover:to-secondary/10 transition-all cursor-pointer group"
            onClick={() => !isLoading && onQuestionClick(question)}
          >
            <div className="flex items-start gap-3">
              <div className="shrink-0 w-6 h-6 rounded-full bg-linear-to-br from-primary to-secondary flex items-center justify-center text-white text-xs font-bold">
                {idx + 1}
              </div>
              <p className="text-sm text-foreground group-hover:text-primary transition-colors flex-1 leading-relaxed">
                {question}
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity h-auto py-1 px-2"
                disabled={isLoading}
              >
                Ask →
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}