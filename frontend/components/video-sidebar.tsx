'use client'

import { useState } from 'react'
import { Play } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Video {
  id: number
  title: string
  duration: string
}

const SAMPLE_VIDEOS: Video[] = [
  { id: 1, title: 'Introduction to CSS Flexbox', duration: '12:34' },
  { id: 2, title: 'CSS Grid Basics and Layout', duration: '18:45' },
  { id: 3, title: 'Responsive Design Fundamentals', duration: '15:22' },
  { id: 4, title: 'Media Queries and Mobile First', duration: '10:56' },
  { id: 5, title: 'Advanced Flexbox Techniques', duration: '20:10' },
  { id: 6, title: 'CSS Custom Properties (Variables)', duration: '14:38' },
  { id: 7, title: 'Animation and Transitions', duration: '16:42' },
  { id: 8, title: 'Bootstrap and Tailwind CSS', duration: '22:15' },
]

interface VideoSidebarProps {
  selectedVideoId: number | null
  onSelectVideo: (videoId: number) => void
}

export function VideoSidebar({ selectedVideoId, onSelectVideo }: VideoSidebarProps) {
  return (
    <div className="hidden lg:flex flex-col w-72 bg-gradient-to-b from-card via-card to-card/80 border-r border-border h-[calc(100vh-4rem)] mt-16 overflow-hidden">
      <div className="p-4 border-b border-border/50">
        <h2 className="text-sm font-semibold text-foreground">Course Videos</h2>
        <p className="text-xs text-muted-foreground mt-1">8 lessons</p>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
        <div className="p-2 space-y-2">
          {SAMPLE_VIDEOS.map((video) => (
            <button
              key={video.id}
              onClick={() => onSelectVideo(video.id)}
              className={cn(
                'w-full text-left p-3 rounded-lg transition-all duration-200',
                'hover:bg-muted/50 group',
                selectedVideoId === video.id
                  ? 'bg-gradient-to-r from-primary/30 to-secondary/20 border border-primary/50'
                  : 'border border-transparent'
              )}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-1 hidden group-hover:block transition-opacity">
                  <Play className="h-4 w-4 text-primary fill-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-primary mb-1">
                    Video {video.id}
                  </div>
                  <h3 className="text-sm text-foreground leading-tight truncate line-clamp-2">
                    {video.title}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1">{video.duration}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
