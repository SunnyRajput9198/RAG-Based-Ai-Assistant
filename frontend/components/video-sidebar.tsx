'use client'

import { useEffect, useState } from 'react'
import { Play, Folder, Loader2, AlertCircle, Layers, MonitorPlay, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

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

  // 🆕 ADD: Expose refresh via window event
  useEffect(() => {
    const handleRefresh = () => fetchVideos()
    window.addEventListener('refreshVideos', handleRefresh)
    return () => window.removeEventListener('refreshVideos', handleRefresh)
  }, [])

  return (
    <aside className="hidden lg:flex flex-col w-80 border-r border-border/50 bg-card/20 backdrop-blur-xl h-[calc(100vh-4rem)] mt-16 overflow-hidden transition-all duration-300">
      {/* HEADER SECTION */}
      <div className="p-6 border-b border-border/40 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-widest text-muted-foreground/80 flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            Curriculum
          </h2>
          {!loading && !error && (
            <Badge variant="secondary" className="bg-primary/10 text-primary border-none font-mono text-[10px]">
              {videos.length} MODULES
            </Badge>
          )}
        </div>
        
        {/* GLOBAL CONTEXT SELECTOR */}
        <button
          onClick={() => onSelectVideo(null)}
          className={cn(
            "w-full flex items-center gap-3 p-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
            selectedVideoId === null
              ? "bg-zinc-900 text-white dark:bg-white dark:text-black shadow-lg"
              : "hover:bg-muted/50 text-foreground"
          )}
        >
          <div className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center shrink-0 transition-colors",
            selectedVideoId === null ? "bg-white/20 dark:bg-black/10" : "bg-primary/10"
          )}>
            <MonitorPlay className={cn("h-5 w-5", selectedVideoId === null ? "text-current" : "text-primary")} />
          </div>
          <div className="text-left">
            <p className="text-sm font-bold leading-none">Full Course</p>
            <p className={cn(
              "text-[10px] mt-1 font-medium opacity-70",
              selectedVideoId === null ? "text-current" : "text-muted-foreground"
            )}>
              Global AI Context
            </p>
          </div>
        </button>
      </div>

      {/* SCROLLABLE VIDEO LIST */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-1">
        {loading ? (
          Array(6).fill(0).map((_, i) => <VideoSkeleton key={i} />)
        ) : error ? (
          <div className="py-12 px-4 text-center space-y-4">
            <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto">
              <AlertCircle className="h-6 w-6 text-destructive" />
            </div>
            <div>
              <p className="text-sm font-bold">Connection Lost</p>
              <p className="text-xs text-muted-foreground mt-1">Unable to sync lessons.</p>
            </div>
            <Button onClick={fetchVideos} variant="outline" size="sm" className="rounded-full px-6">
              <Loader2 className="h-3 w-3 mr-2" /> Retry
            </Button>
          </div>
        ) : (
          videos.map((video) => (
            <button
              key={video.id}
              onClick={() => onSelectVideo(video.id)}
              className={cn(
                "w-full group relative p-3 rounded-xl transition-all duration-200 border border-transparent",
                selectedVideoId === video.id
                  ? "bg-card border-border shadow-sm ring-1 ring-primary/20"
                  : "hover:bg-muted/30"
              )}
            >
              <div className="flex gap-4">
                <div className="relative shrink-0">
                  <div className={cn(
                    "w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300",
                    selectedVideoId === video.id
                      ? "bg-primary text-white scale-110 rotate-3 shadow-md shadow-primary/20"
                      : "bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary"
                  )}>
                    <Play className={cn("h-4 w-4 fill-current", selectedVideoId === video.id ? "opacity-100" : "opacity-40")} />
                  </div>
                </div>

                <div className="min-w-0 text-left flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className={cn(
                      "text-[10px] font-bold tracking-tighter uppercase",
                      selectedVideoId === video.id ? "text-primary" : "text-muted-foreground/50"
                    )}>
                      Lesson {video.id.toString().padStart(2, '0')}
                    </span>
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground/40 font-mono">
                      <Clock className="h-3 w-3" />
                      {video.duration}
                    </div>
                  </div>
                  <p className={cn(
                    "text-sm font-semibold truncate mt-0.5 transition-colors",
                    selectedVideoId === video.id ? "text-foreground" : "text-muted-foreground group-hover:text-foreground"
                  )}>
                    {video.title}
                  </p>
                </div>
              </div>
            </button>
          ))
        )}
      </div>

      {/* FOOTER - USER INFO OR SETTINGS */}
      <div className="p-4 border-t border-border/40 bg-muted/10">
        <div className="rounded-xl p-3 bg-linear-to-br from-primary/5 to-secondary/5 border border-primary/10">
          <p className="text-[10px] font-bold text-primary uppercase tracking-widest mb-1">AI Tip</p>
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            Selecting a video limits the AI's search to that specific lesson's transcript.
          </p>
        </div>
      </div>
    </aside>
  )
}