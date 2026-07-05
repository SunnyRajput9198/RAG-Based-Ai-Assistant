'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  Play, Loader2, AlertCircle, Layers, MonitorPlay,
  FileText, Trash2, RefreshCw,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from '@/components/ui/alert-dialog'

const API = 'http://localhost:8000'

interface Resource {
  id: string
  title: string
  type: 'video' | 'pdf'
  chunk_count?: number
  indexed_at?: string
  video_url?: string | null
  file_size_bytes?: number | null
}

interface VideoSidebarProps {
  selectedVideoId: string | null
  onSelectVideo: (id: string | null) => void
}

type Tab = 'video' | 'pdf'

function Skeleton() {
  return (
    <div className="w-full p-3 rounded-lg animate-pulse">
      <div className="flex gap-3">
        <div className="w-8 h-8 rounded-lg bg-muted" />
        <div className="flex-1 space-y-2">
          <div className="h-3 bg-muted rounded w-16" />
          <div className="h-4 bg-muted rounded w-full" />
        </div>
      </div>
    </div>
  )
}

function formatBytes(bytes?: number | null) {
  if (!bytes) return null
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function VideoSidebar({ selectedVideoId, onSelectVideo }: VideoSidebarProps) {
  const [videos, setVideos] = useState<Resource[]>([])
  const [pdfs, setPdfs] = useState<Resource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('video')
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fetchResources = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const [vRes, pRes] = await Promise.all([
        fetch(`${API}/videos`),
        fetch(`${API}/documents`),
      ])
      if (!vRes.ok || !pRes.ok) throw new Error()
      setVideos(await vRes.json())
      setPdfs(await pRes.json())
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchResources() }, [fetchResources])

  // Listen for refresh events from video-processor / pdf_upload
  useEffect(() => {
    const handler = () => fetchResources()
    window.addEventListener('refreshVideos', handler)
    window.addEventListener('refreshDocuments', handler)
    return () => {
      window.removeEventListener('refreshVideos', handler)
      window.removeEventListener('refreshDocuments', handler)
    }
  }, [fetchResources])

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try {
      await fetch(`${API}/resource/${encodeURIComponent(id)}`, { method: 'DELETE' })
      if (selectedVideoId === id) onSelectVideo(null)
      await fetchResources()
    } catch {
      console.error('Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  const resources = activeTab === 'video' ? videos : pdfs

  return (
    <aside className="hidden lg:flex flex-col w-80 border-r border-border/50 bg-card/20 backdrop-blur-xl h-[calc(100vh-4rem)] overflow-hidden transition-all duration-300">

      {/* Header */}
      <div className="p-5 border-b border-border/40 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-widest text-muted-foreground/80 flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            Library
          </h2>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={fetchResources} disabled={loading}>
            <RefreshCw className={cn('h-3 w-3', loading && 'animate-spin')} />
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-muted/40 rounded-xl p-1">
          {(['video', 'pdf'] as Tab[]).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeTab === tab
                  ? 'bg-card shadow text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {tab === 'video'
                ? <><Play className="h-3 w-3" /> Lessons <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4">{videos.length}</Badge></>
                : <><FileText className="h-3 w-3" /> Docs <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4">{pdfs.length}</Badge></>
              }
            </button>
          ))}
        </div>

        {/* All context button */}
        <button
          onClick={() => onSelectVideo(null)}
          className={cn(
            'w-full flex items-center gap-3 p-3 rounded-xl transition-all duration-200',
            selectedVideoId === null
              ? 'bg-zinc-900 text-white dark:bg-white dark:text-black shadow-lg'
              : 'hover:bg-muted/50 text-foreground'
          )}
        >
          <div className={cn(
            'w-9 h-9 rounded-lg flex items-center justify-center shrink-0',
            selectedVideoId === null ? 'bg-white/20 dark:bg-black/10' : 'bg-primary/10'
          )}>
            <MonitorPlay className={cn('h-4 w-4', selectedVideoId === null ? 'text-current' : 'text-primary')} />
          </div>
          <div className="text-left">
            <p className="text-sm font-bold leading-none">All Sources</p>
            <p className={cn('text-[10px] mt-0.5 font-medium opacity-70', selectedVideoId === null ? 'text-current' : 'text-muted-foreground')}>
              Global AI Context
            </p>
          </div>
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto sidebar-scroll p-3 space-y-1">
        {loading ? (
          Array(5).fill(0).map((_, i) => <Skeleton key={i} />)
        ) : error ? (
          <div className="py-12 px-4 text-center space-y-4">
            <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto">
              <AlertCircle className="h-6 w-6 text-destructive" />
            </div>
            <p className="text-sm font-bold">Connection Lost</p>
            <Button onClick={fetchResources} variant="outline" size="sm" className="rounded-full px-6">
              <Loader2 className="h-3 w-3 mr-2" /> Retry
            </Button>
          </div>
        ) : resources.length === 0 ? (
          <div className="py-12 text-center text-xs text-muted-foreground">
            {activeTab === 'video' ? 'No videos indexed yet.' : 'No documents uploaded yet.'}
          </div>
        ) : (
          resources.map((resource, idx) => (
            <div
              key={resource.id}
              className={cn(
                'group relative w-full p-3 rounded-xl transition-all duration-200 border border-transparent',
                selectedVideoId === resource.id
                  ? 'bg-card border-border shadow-sm ring-1 ring-primary/20'
                  : 'hover:bg-muted/30'
              )}
            >
              <button
                className="w-full text-left"
                onClick={() => onSelectVideo(resource.id)}
              >
                <div className="flex gap-3 items-start">
                  <div className={cn(
                    'w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-all',
                    selectedVideoId === resource.id
                      ? 'bg-primary text-white shadow-md shadow-primary/20 scale-110 rotate-3'
                      : 'bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary'
                  )}>
                    {resource.type === 'pdf'
                      ? <FileText className="h-4 w-4" />
                      : <Play className={cn('h-4 w-4 fill-current', selectedVideoId === resource.id ? 'opacity-100' : 'opacity-40')} />
                    }
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className={cn(
                      'text-[10px] font-bold tracking-tight uppercase',
                      selectedVideoId === resource.id ? 'text-primary' : 'text-muted-foreground/50'
                    )}>
                      {resource.type === 'video' ? `Lesson ${String(idx + 1).padStart(2, '0')}` : 'Document'}
                    </span>
                    <p className={cn(
                      'text-sm font-semibold truncate mt-0.5',
                      selectedVideoId === resource.id ? 'text-foreground' : 'text-muted-foreground group-hover:text-foreground'
                    )}>
                      {resource.title}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {resource.chunk_count != null && (
                        <span className="text-[10px] text-muted-foreground/50 font-mono">
                          {resource.chunk_count} chunks
                        </span>
                      )}
                      {resource.file_size_bytes && (
                        <span className="text-[10px] text-muted-foreground/50 font-mono">
                          {formatBytes(resource.file_size_bytes)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>

              {/* Delete button */}
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <button className={cn(
                    'absolute top-2 right-2 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all',
                    'hover:bg-destructive/10 hover:text-destructive text-muted-foreground'
                  )}>
                    {deletingId === resource.id
                      ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      : <Trash2 className="h-3.5 w-3.5" />
                    }
                  </button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete "{resource.title}"?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will remove all {resource.chunk_count ?? ''} chunks from Qdrant and the resource registry. This cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => handleDelete(resource.id)}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          ))
        )}
      </div>

      {/* Footer tip */}
      <div className="p-4 border-t border-border/40">
        <div className="rounded-xl p-3 bg-gradient-to-br from-primary/5 to-secondary/5 border border-primary/10">
          <p className="text-[10px] font-bold text-primary uppercase tracking-widest mb-1">AI Tip</p>
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            Select a specific lesson or document to focus the AI's search context.
          </p>
        </div>
      </div>
    </aside>
  )
}
