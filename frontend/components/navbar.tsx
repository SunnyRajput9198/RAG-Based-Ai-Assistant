'use client'

import { useEffect, useState } from 'react'
import { Moon, Sun, Sparkles } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'
import { PdfUpload } from '@/components/pdf_upload'
import { motion } from 'framer-motion'
import { VideoProcessor } from '@/components/video-processor'
export function Navbar() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handlePdfUploadComplete = () => {
    console.log('PDF uploaded successfully!')
  }

  return (
    <nav className="fixed top-0 left-0 right-0 h-16 border-b border-white/5 bg-background/60 backdrop-blur-md z-50 transition-all duration-300">
      <div className="h-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">

        {/* Logo Section with Glow Effect */}
        <div className="flex items-center gap-4 group cursor-pointer">
          <div className="relative">
            <div className="absolute -inset-1 bg-linear-to-r from-primary to-secondary rounded-lg blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative w-9 h-9 rounded-lg bg-zinc-950 flex items-center justify-center border border-white/10 shadow-2xl">
              <span className="text-transparent bg-clip-text bg-linear-to-br from-white to-zinc-500 font-bold text-lg">
                E
              </span>
            </div>
          </div>

          <div className="flex flex-col leading-tight">
            <div className="flex items-center gap-1.5">
              <h1 className="text-md font-semibold tracking-tight text-foreground">
                EduBot
              </h1>
              <Sparkles className="w-3 h-3 text-primary animate-pulse" />
            </div>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/80 font-medium hidden sm:block">
              Intelligent RAG
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:block">
            <VideoProcessor />
            <PdfUpload onUploadComplete={handlePdfUploadComplete} />
          </div>

          <div className="h-6 w-px bg-white/10 mx-1 hidden sm:block" />

          {/* Theme Toggle with Animation */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="relative overflow-hidden rounded-full hover:bg-white/5 border border-transparent hover:border-white/10 transition-all"
          >
            {mounted ? (
              theme === 'dark' ? (
                <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all" />
              ) : (
                <Moon className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all" />
              )
            ) : (
              <Sun className="h-[1.2rem] w-[1.2rem] opacity-0" />
            )}
            <span className="sr-only">Toggle theme</span>
          </Button>

          {/* Profile/User Placeholder (Optional but adds "Completeness") */}
          <div className="w-8 h-8 rounded-full bg-linear-to-tr from-zinc-800 to-zinc-700 border border-white/10 flex items-center justify-center text-[10px] font-medium">
            JD
          </div>
        </div>
      </div>
    </nav>
  )
}