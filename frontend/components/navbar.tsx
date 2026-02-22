'use client'

import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'

export function Navbar() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <nav className="fixed top-0 left-0 right-0 h-16 border-b border-border bg-gradient-to-r from-card to-card/80 backdrop-blur-xl z-50">
      <div className="h-full max-w-full px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary via-secondary to-primary flex items-center justify-center text-white font-bold text-sm">
            E
          </div>
          <div className="flex flex-col">
            <h1 className="text-lg font-bold bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text text-transparent">
              EduBot
            </h1>
            <p className="text-xs text-muted-foreground hidden sm:block">
              RAG Teaching Assistant
            </p>
          </div>
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="hover:bg-muted"
        >
          {mounted ? (
            theme === 'dark' ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )
          ) : (
            <Sun className="h-5 w-5" />
          )}
        </Button>
      </div>
    </nav>
  )
}