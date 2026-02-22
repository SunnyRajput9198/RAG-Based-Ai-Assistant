'use client'

import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

interface Source {
  videoId: number
  videoTitle: string
  timestamp: string
}

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
}

export function ChatMessage({ role, content, sources }: ChatMessageProps) {
  if (role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-md lg:max-w-2xl bg-gradient-to-r from-primary/80 to-secondary/60 text-primary-foreground rounded-xl px-4 py-3 shadow-lg">
          <p className="text-sm leading-relaxed">{content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-md lg:max-w-2xl">
        <div className="bg-card border border-border rounded-xl px-4 py-3 shadow-lg mb-3">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-xs font-bold">
              AI
            </div>
            <p className="text-sm leading-relaxed text-foreground pt-0.5">{content}</p>
          </div>
        </div>

        {sources && sources.length > 0 && (
          <div className="pl-11">
            <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
              Sources
            </p>
            <div className="space-y-2">
              {sources.map((source, idx) => (
                <Card
                  key={idx}
                  className="p-3 bg-card/50 border border-border/60 hover:border-primary/50 hover:bg-card/80 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-foreground truncate">
                        Video {source.videoId}: {source.videoTitle}
                      </p>
                    </div>
                    <Badge
                      variant="secondary"
                      className="flex-shrink-0 bg-gradient-to-r from-primary/30 to-secondary/20 text-primary border border-primary/30 hover:bg-primary/40 transition-colors whitespace-nowrap"
                    >
                      {source.timestamp}
                    </Badge>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
