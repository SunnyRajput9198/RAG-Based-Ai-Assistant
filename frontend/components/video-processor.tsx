'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Youtube, Loader2, X, CheckCircle2 } from 'lucide-react'

export function VideoProcessor() {
  const [url, setUrl] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [result, setResult] = useState<any>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const processVideo = () => {
    if (!url.trim()) return
    
    setIsProcessing(true)
    setProgress(0)
    setStatus('Connecting...')
    setResult(null)
    
    const ws = new WebSocket('ws://localhost:8000/ws/process-video')
    wsRef.current = ws
    
    ws.onopen = () => {
      setStatus('Sending URL...')
      ws.send(url.trim())
    }
    
    ws.onmessage = (event) => {
      const message = event.data
      setStatus(message)
      
      if (message.includes('Starting')) setProgress(5)
      else if (message.includes('Downloading')) setProgress(20)
      else if (message.includes('Transcribing') && message.includes('%')) {
        const match = message.match(/(\d+)%/)
        if (match) setProgress(30 + (parseInt(match[1]) * 0.5))
      }
      else if (message.includes('Creating embeddings')) setProgress(85)
      else if (message.includes('Saving')) setProgress(95)
      else if (message.includes('COMPLETE')) setProgress(100)
      
      try {
        const data = JSON.parse(message)
        if (data.status === 'complete') {
          setProgress(100)
          setResult({ success: true, title: data.title, chunks: data.chunks })
          setIsProcessing(false)
          wsRef.current = null
          
          // 🆕 TRIGGER SIDEBAR REFRESH
          window.dispatchEvent(new Event('refreshVideos'))
        }
      } catch (e) {}
    }
    
    ws.onerror = () => {
      setStatus('Connection error!')
      setResult({ success: false })
      setIsProcessing(false)
      wsRef.current = null
    }
    
    ws.onclose = () => {
      wsRef.current = null
    }
  }

  const cancelProcessing = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsProcessing(false)
    setStatus('❌ Cancelled by user')
    setProgress(0)
  }

  const handleReset = () => {
    setUrl('')
    setProgress(0)
    setStatus('')
    setResult(null)
    setIsProcessing(false)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Youtube className="h-4 w-4" />
          Process Video
        </Button>
      </DialogTrigger>
      
      <DialogContent className="sm:max-w-125">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Youtube className="h-5 w-5 text-red-500" />
            Process YouTube Video
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <Input
            placeholder="https://youtu.be/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isProcessing}
          />
          
          {(isProcessing || result) && (
            <div className="space-y-4 p-4 border rounded-lg bg-card">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isProcessing && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
                  {result?.success && <CheckCircle2 className="h-4 w-4 text-green-600" />}
                  <span className="text-sm font-medium">
                    {result ? (result.success ? 'Complete!' : 'Failed') : 'Processing...'}
                  </span>
                </div>
                
                {isProcessing && (
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={cancelProcessing}
                    className="h-8 gap-2 text-destructive hover:text-destructive"
                  >
                    <X className="h-4 w-4" />
                    Cancel
                  </Button>
                )}
              </div>
              
              <div className="space-y-2">
                <Progress value={progress} />
                <p className="text-xs text-center text-muted-foreground">
                  {Math.round(progress)}%
                </p>
              </div>
              
              <div className="rounded bg-muted/50 p-3">
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {status}
                </p>
              </div>
              
              {result?.success && (
                <div className="rounded-lg bg-primary/5 border border-primary/20 p-3">
                  <p className="text-sm font-medium">✅ {result.title}</p>
                  <p className="text-xs text-muted-foreground">{result.chunks} chunks</p>
                </div>
              )}
            </div>
          )}
          
          <div className="flex gap-2 justify-end">
            {result ? (
              <>
                <Button variant="outline" onClick={handleReset}>
                  Process Another
                </Button>
                <Button onClick={() => setIsOpen(false)}>
                  Close
                </Button>
              </>
            ) : (
              <Button 
                onClick={processVideo}
                disabled={isProcessing || !url.trim()}
                className="gap-2"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Youtube className="h-4 w-4" />
                    Start
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}