'use client'

import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Check, Copy, FileText, Video, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface Source {
  videoId: string
  videoTitle: string
  timestamp: string
  timestamp_seconds?: number  // 🆕 For video links
  similarity: number
  text_preview: string
  source_type?: 'video' | 'pdf'
  video_url?: string | null  // 🆕 YouTube URL
}

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
}

function CodeBlock({ children, inline }: { children: string; inline?: boolean }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(children)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (inline) {
    return (
      <code className="px-1.5 py-0.5 rounded bg-muted text-primary font-mono text-xs border border-border/50">
        {children}
      </code>
    )
  }

  return (
    <div className="relative group">
      <Button
        variant="ghost"
        size="icon"
        onClick={handleCopy}
        className="absolute top-2 right-2 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity bg-background/80 hover:bg-background"
      >
        {copied ? (
          <Check className="h-4 w-4 text-green-500" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
      </Button>
      <pre className="p-4 rounded-lg bg-muted/70 border border-border text-xs font-mono overflow-x-auto">
        <code>{children}</code>
      </pre>
    </div>
  )
}

export function ChatMessage({ role, content, sources }: ChatMessageProps) {
  // USER MESSAGE
  if (role === 'user') {
    return (
      <div className="flex justify-end mb-4 animate-in slide-in-from-right duration-300">
        <div className="max-w-[80%] lg:max-w-2xl bg-gradient-to-r from-primary/90 to-secondary/70 text-primary-foreground rounded-2xl rounded-tr-sm px-5 py-3 shadow-lg">
          <p className="text-sm leading-relaxed">{content}</p>
        </div>
      </div>
    )
  }

  // ASSISTANT MESSAGE
  const isTyping = content === ''

  return (
    <div className="flex justify-start mb-6 animate-in slide-in-from-left duration-300">
      <div className="max-w-[85%] lg:max-w-3xl w-full">
        <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-5 py-4 shadow-lg mb-3 hover:shadow-xl transition-shadow">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-xs font-bold shadow-md">
              AI
            </div>

            {isTyping ? (
              <div className="flex gap-1 pt-2">
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-secondary animate-bounce [animation-delay:0.1s]" />
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:0.2s]" />
              </div>
            ) : (
              <div className="flex-1 prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown
                  components={{
                    p: ({ children }) => (
                      <p className="mb-3 last:mb-0 leading-relaxed text-foreground">
                        {children}
                      </p>
                    ),
                    code: ({ inline, children, ...props }: any) => (
                      <CodeBlock inline={inline}>
                        {String(children).replace(/\n$/, '')}
                      </CodeBlock>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-disc list-inside space-y-1 mb-3 text-foreground">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal list-inside space-y-1 mb-3 text-foreground">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className="text-foreground leading-relaxed">{children}</li>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold text-foreground">{children}</strong>
                    ),
                    em: ({ children }) => (
                      <em className="italic text-muted-foreground">{children}</em>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-base font-semibold text-foreground mt-4 mb-2">
                        {children}
                      </h3>
                    ),
                    h4: ({ children }) => (
                      <h4 className="text-sm font-semibold text-foreground mt-3 mb-1">
                        {children}
                      </h4>
                    ),
                  }}
                >
                  {content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </div>

        {/* SOURCES SECTION - Updated with clickable timestamps */}
        {sources && sources.length > 0 && (
          <div className="pl-11 animate-in fade-in duration-500">
            <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide flex items-center gap-2">
              <span className="w-1 h-1 rounded-full bg-primary" />
              Sources ({sources.length})
            </p>
            <div className="space-y-2">
              {sources.map((source, idx) => {
                // 🆕 Build clickable YouTube link with timestamp
                const videoLink = source.video_url && source.timestamp_seconds !== undefined
                  ? `${source.video_url}&t=${source.timestamp_seconds}s`
                  : null

                return (
                  <Card
                    key={idx}
                    className="p-3 bg-card/50 border border-border/60 hover:border-primary/50 hover:bg-card/80 hover:shadow-md transition-all group"
                  >
                    {/* Header: Icon, Title and Similarity Score */}
                    <div className="flex items-center justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {/* Source Type Icon */}
                        {source.source_type === 'pdf' ? (
                          <FileText className="h-4 w-4 text-orange-500 flex-shrink-0" />
                        ) : (
                          <Video className="h-4 w-4 text-blue-500 flex-shrink-0" />
                        )}
                        <p className="text-xs font-medium text-foreground truncate group-hover:text-primary transition-colors">
                          {source.videoTitle}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {/* Similarity Badge */}
                        <Badge
                          variant="outline"
                          className="bg-primary/10 text-primary border-primary/30 font-semibold text-xs"
                        >
                          {(source.similarity * 100).toFixed(1)}%
                        </Badge>
                        
                        {/* Timestamp/Page Badge - Clickable for videos */}
                        {videoLink ? (
                          <a
                            href={videoLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-block"
                          >
                            <Badge
                              variant="secondary"
                              className="bg-gradient-to-r from-blue-500/30 to-purple-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/40 hover:bg-blue-500/40 hover:scale-105 transition-all cursor-pointer whitespace-nowrap text-xs flex items-center gap-1"
                            >
                              ▶ {source.timestamp}
                              <ExternalLink className="h-3 w-3" />
                            </Badge>
                          </a>
                        ) : (
                          <Badge
                            variant="secondary"
                            className="bg-gradient-to-r from-primary/30 to-secondary/20 text-primary border border-primary/30 whitespace-nowrap text-xs"
                          >
                            {source.source_type === 'pdf' ? '📖' : '⏱'} {source.timestamp}
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Text Preview */}
                    <p className="text-xs text-muted-foreground leading-relaxed bg-muted/30 p-2 rounded border border-border/30">
                      {source.text_preview}
                    </p>
                    
                    {/* "Watch at this moment" button for videos */}
                    {videoLink && (
                      <a
                        href={videoLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-flex"
                      >
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs gap-1.5 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-500/10"
                        >
                          <ExternalLink className="h-3 w-3" />
                          Watch at this moment
                        </Button>
                      </a>
                    )}
                  </Card>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}