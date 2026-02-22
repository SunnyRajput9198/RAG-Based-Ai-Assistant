'use client'

import { useEffect, useState } from 'react'
import { Play, Folder, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface Video {
  id: number
  title: string
  duration: string
}

interface VideoSidebarProps {
  selectedVideoId: number | null
  onSelectVideo: (id: number | null) => void
}

function VideoSkeleton() {
  return (
    <div className="w-full p-3 rounded-lg border-2 border-transparent animate-pulse">
      <div className="flex gap-3">
        <div className="w-8 h-8 rounded-lg bg-muted" />
        <div className="flex-1 space-y-2">
          <div className="h-3 bg-muted rounded w-16" />
          <div className="h-4 bg-muted rounded w-full" />
          <div className="h-3 bg-muted rounded w-12" />
        </div>
      </div>
    </div>
  )
}

export function VideoSidebar({ selectedVideoId, onSelectVideo }: VideoSidebarProps) {
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const fetchVideos = async () => {
    setLoading(true)
    setError(false)
    try {
      const res = await fetch('http://localhost:8000/videos')
      if (!res.ok) throw new Error('Failed to load videos')
      const data = await res.json()
      setVideos(data)
    } catch (err) {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchVideos()
  }, [])

  return (
    <aside className="hidden lg:flex flex-col w-72 border-r border-border bg-card/30 backdrop-blur-sm h-[calc(100vh-4rem)] mt-16 overflow-hidden">
      {/* HEADER - Fixed */}
      <div className="flex-shrink-0 p-4 border-b border-border bg-gradient-to-r from-card to-card/80">
        <h2 className="font-semibold text-foreground flex items-center gap-2">
          <Folder className="h-4 w-4 text-primary" />
          Course Videos
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          {loading ? (
            'Loading...'
          ) : error ? (
            'Failed to load'
          ) : (
            <>
              {videos.length} lessons • {selectedVideoId ? 'Filtered' : 'All videos'}
            </>
          )}
        </p>
      </div>

      {/* VIDEO LIST - Scrollable with custom scrollbar */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden sidebar-scroll">
        <div className="p-3 space-y-2 pb-4">
          {loading ? (
            // LOADING STATE
            <>
              <VideoSkeleton />
              <VideoSkeleton />
              <VideoSkeleton />
              <VideoSkeleton />
              <VideoSkeleton />
            </>
          ) : error ? (
            // ERROR STATE
            <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
              <AlertCircle className="h-8 w-8 text-destructive mb-2" />
              <p className="text-sm font-medium text-foreground mb-1">
                Failed to load videos
              </p>
              <p className="text-xs text-muted-foreground mb-3">
                Check your connection and try again
              </p>
              <Button
                onClick={fetchVideos}
                variant="outline"
                size="sm"
                className="gap-2"
              >
                <Loader2 className="h-3 w-3" />
                Retry
              </Button>
            </div>
          ) : (
            // VIDEOS LIST
            <>
              {/* ALL VIDEOS OPTION */}
              <button
                onClick={() => onSelectVideo(null)}
                className={cn(
                  'w-full text-left p-3 rounded-lg transition-all group',
                  'hover:bg-muted/70 hover:shadow-sm',
                  selectedVideoId === null
                    ? 'bg-gradient-to-r from-primary/20 to-secondary/10 border-2 border-primary/50 shadow-md'
                    : 'border-2 border-transparent'
                )}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0 shadow-sm">
                    <Folder className="h-4 w-4 text-white" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-foreground">All Videos</p>
                    <p className="text-xs text-muted-foreground">
                      Search across entire course
                    </p>
                  </div>
                </div>
              </button>

              {/* INDIVIDUAL VIDEOS */}
              {videos.map((video) => (
                <button
                  key={video.id}
                  onClick={() => onSelectVideo(video.id)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg transition-all group',
                    'hover:bg-muted/70 hover:shadow-sm',
                    selectedVideoId === video.id
                      ? 'bg-gradient-to-r from-primary/20 to-secondary/10 border-2 border-primary/50 shadow-md'
                      : 'border-2 border-transparent'
                  )}
                >
                  <div className="flex gap-3">
                    <div
                      className={cn(
                        'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm transition-all',
                        selectedVideoId === video.id
                          ? 'bg-gradient-to-br from-primary to-secondary'
                          : 'bg-muted group-hover:bg-primary/20'
                      )}
                    >
                      <Play
                        className={cn(
                          'h-4 w-4 transition-colors',
                          selectedVideoId === video.id
                            ? 'text-white'
                            : 'text-muted-foreground group-hover:text-primary'
                        )}
                      />
                    </div>

                    <div className="min-w-0 flex-1">
                      <p
                        className={cn(
                          'text-xs font-semibold mb-0.5',
                          selectedVideoId === video.id
                            ? 'text-primary'
                            : 'text-muted-foreground'
                        )}
                      >
                        Video {video.id}
                      </p>
                      <p className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                        {video.title}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {video.duration}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </>
          )}
        </div>
      </div>
    </aside>
  )
}