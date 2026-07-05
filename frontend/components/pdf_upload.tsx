'use client'

import { useState, useCallback } from 'react'
import { Upload, FileText, X, CheckCircle2, AlertCircle, FileUp, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

interface UploadResult {
  success: boolean
  title?: string
  pdf_id?: string
  chunks?: number
  error?: string
}

interface PdfUploadProps {
  onUploadComplete?: () => void
}

export function PdfUpload({ onUploadComplete }: PdfUploadProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0 && files[0].type === 'application/pdf') {
      setSelectedFile(files[0])
      setResult(null)
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setSelectedFile(files[0])
      setResult(null)
    }
  }, [])

  const handleUpload = async () => {
    if (!selectedFile) return
    setIsUploading(true)
    setUploadProgress(0)
    setResult(null)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 5, 95))
      }, 150)

      const response = await fetch('http://localhost:8000/upload-pdf', {
        method: 'POST',
        body: formData,
      })

      clearInterval(progressInterval)
      setUploadProgress(100)
      const data = await response.json()

      if (response.ok && data.success) {
        setResult({ success: true, title: data.title, pdf_id: data.pdf_id, chunks: data.chunks })
        window.dispatchEvent(new Event('refreshDocuments'))
        setTimeout(() => {
          onUploadComplete?.()
          handleReset()
          setIsOpen(false)
        }, 2500)
      } else {
        setResult({ success: false, error: data.detail || 'Upload failed' })
      }
    } catch (error) {
      setResult({ success: false, error: 'Network error: Check your connection' })
    } finally {
      setIsUploading(false)
    }
  }

  const handleReset = () => {
    setSelectedFile(null)
    setResult(null)
    setUploadProgress(0)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          className="group relative overflow-hidden h-9 px-4 gap-2 bg-zinc-900 text-white dark:bg-white dark:text-black hover:opacity-90 transition-all border-none"
        >
          <FileUp className="h-4 w-4 transition-transform group-hover:-translate-y-1" />
          <span className="text-xs font-semibold">Upload PDF</span>
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-md border-border/40 bg-card/95 backdrop-blur-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold tracking-tight">Add Knowledge</DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground/70 italic">
            Your PDF will be vectorized into searchable context chunks.
          </DialogDescription>
        </DialogHeader>

        <div className="py-2">
          {/* File Drop Zone */}
          {!selectedFile && !result && (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={cn(
                "group relative border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-300",
                isDragging 
                  ? "border-primary bg-primary/5 scale-[0.98]" 
                  : "border-border/60 hover:border-primary/40 hover:bg-muted/30"
              )}
            >
              <input type="file" accept=".pdf" onChange={handleFileSelect} className="hidden" id="pdf-upload" />
              <label htmlFor="pdf-upload" className="cursor-pointer flex flex-col items-center">
                <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Upload className="h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
                <p className="text-sm font-semibold text-foreground">Drop your syllabus or notes here</p>
                <p className="text-[11px] text-muted-foreground mt-1.5 uppercase tracking-wider font-medium">
                  PDF up to 50MB
                </p>
              </label>
            </div>
          )}

          {/* Processing / Selected File Card */}
          {selectedFile && !result && (
            <div className="space-y-4">
              <Card className="p-4 border-border/40 bg-muted/20 shadow-none">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-primary/10 rounded-xl">
                    <FileText className="h-6 w-6 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold truncate text-foreground">{selectedFile.name}</p>
                    <p className="text-[10px] font-mono text-muted-foreground uppercase">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  {!isUploading && (
                    <Button variant="ghost" size="icon" onClick={handleReset} className="rounded-full hover:bg-destructive/10 hover:text-destructive">
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                {isUploading && (
                  <div className="mt-6 space-y-3">
                    <div className="flex justify-between text-[10px] font-bold uppercase tracking-tighter">
                      <span className="text-primary animate-pulse">Chunking & Vectorizing...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-1.5 bg-muted" />
                  </div>
                )}
              </Card>

              {!isUploading && (
                <Button onClick={handleUpload} className="w-full h-11 rounded-xl font-bold bg-primary shadow-lg shadow-primary/20">
                  Confirm & Process
                </Button>
              )}
            </div>
          )}

          {/* Success / Error States */}
          {result && (
            <div className={cn(
              "rounded-2xl p-6 text-center animate-in zoom-in-95 duration-300",
              result.success ? "bg-green-500/5 border border-green-500/20" : "bg-red-500/5 border border-red-500/20"
            )}>
              {result.success ? (
                <div className="space-y-3">
                  <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto">
                    <CheckCircle2 className="h-6 w-6 text-green-500" />
                  </div>
                  <h3 className="text-md font-bold text-foreground">Indexing Complete</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Successfully generated <span className="text-primary font-mono font-bold">{result.chunks}</span> searchable vectors from your document.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <AlertCircle className="h-10 w-10 text-destructive mx-auto" />
                  <h3 className="text-md font-bold text-foreground">Upload Blocked</h3>
                  <p className="text-xs text-muted-foreground">{result.error}</p>
                  <Button onClick={handleReset} variant="outline" size="sm" className="mt-2">Try Again</Button>
                </div>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}