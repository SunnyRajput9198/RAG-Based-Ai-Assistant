# EduBot - AI Teaching Assistant

A modern, premium AI-powered teaching assistant chat interface built with Next.js, React, and Tailwind CSS. EduBot features a sophisticated dark theme with blue and purple gradients, designed to provide an exceptional learning experience similar to Khan Academy or Coursera.

## Features

### 🎯 Core Features
- **Full-Screen Chat Application** - Immersive conversational interface
- **Video Course Sidebar** - Browse and select from course videos
- **RAG Teaching Assistant** - Get AI-powered answers with source citations
- **Dark/Light Theme Toggle** - Seamless theme switching
- **Fully Responsive Design** - Works perfectly on mobile, tablet, and desktop

### 💬 Chat Interface
- **User Messages** - Ask questions about course material
- **AI Responses** - Get detailed explanations with proper formatting
- **Source Citations** - Each answer includes video sources with timestamps
- **Suggested Questions** - Quick-start prompts for common topics
- **Loading States** - Smooth animation while AI is processing

### 📹 Video Management
- **Video Sidebar** - Browse 8 sample course videos
- **Video Selection** - Click to highlight and select videos
- **Metadata** - See video titles and durations at a glance
- **Mobile Menu** - Accessible on smaller screens via menu button
- **Responsive Scrolling** - Elegant scrollbar styling

### 🎨 Design Highlights
- **Premium Aesthetic** - Inspired by top EdTech platforms
- **Blue & Purple Gradient Accents** - Modern, professional color scheme
- **Smooth Animations** - Polished transitions and interactions
- **Accessible Typography** - Clear hierarchy and readability
- **Dark Mode Optimized** - Easy on the eyes with proper contrast

## Project Structure

```
├── app/
│   ├── layout.tsx           # Root layout with theme provider
│   ├── globals.css          # Global styles and design tokens
│   └── page.tsx             # Main chat interface page
├── components/
│   ├── navbar.tsx           # Top navigation bar
│   ├── video-sidebar.tsx    # Desktop video list sidebar
│   ├── mobile-sidebar.tsx   # Mobile/tablet video menu
│   ├── chat-interface.tsx   # Main chat display area
│   ├── chat-message.tsx     # Individual message component
│   ├── chat-input.tsx       # Message input with suggestions
│   ├── theme-provider.tsx   # Next-themes integration
│   └── ui/                  # shadcn/ui components
├── lib/
│   └── utils.ts             # Utility functions
├── tailwind.config.ts       # Tailwind CSS configuration
└── postcss.config.mjs       # PostCSS configuration
```

## Technology Stack

- **Framework**: Next.js 16 (App Router)
- **UI Components**: shadcn/ui
- **Styling**: Tailwind CSS 4 with semantic design tokens
- **Theme Management**: next-themes
- **Icons**: Lucide React
- **Fonts**: Geist (Google Fonts)
- **Analytics**: Vercel Analytics

## Getting Started

### Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

```bash
npm run build
npm start
```

## Usage

### Chat with the AI
1. Select a video from the sidebar (or use the mobile menu)
2. Type your question in the input field
3. Click "Send" or press Enter to submit
4. View the AI response with source citations
5. Use suggested questions for quick access to common topics

### Theme Switching
- Click the sun/moon icon in the navbar to toggle between light and dark themes
- Your theme preference persists across sessions

### Mobile Experience
- On smaller screens, tap the menu icon to view the video list
- The chat interface scales beautifully for all screen sizes
- Input and navigation are touch-friendly

## Customization

### Design Tokens
Edit `app/globals.css` to customize:
- Color scheme (primary, secondary, accent colors)
- Typography and spacing
- Border radius and other radius values
- Sidebar styling

### Sample Data
Replace the hardcoded responses in `app/page.tsx` with your actual:
- Video list from your database
- AI responses from your backend API
- Source citations from your knowledge base

### Adding Real API Integration
1. Replace the sample responses in `page.tsx` with actual API calls
2. Connect to your backend RAG system
3. Implement real-time video streaming (optional)
4. Add user authentication if needed

## Features to Extend

- User authentication and session management
- Save chat history to database
- Bookmark favorite answers
- Download chat transcripts
- Code syntax highlighting in responses
- Search course videos
- Transcript search across videos
- AI-powered quiz generation
- Personalized learning paths
- Dark mode animations

## Performance Optimizations

- Server-side rendering where appropriate
- Client-side state management for chat
- Optimized image loading
- Efficient CSS with Tailwind utilities
- Smooth scrolling with native CSS

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

Created with v0 by Vercel. Free to use and modify for your projects.

## Support

For issues or questions about the codebase, refer to the official documentation:
- [Next.js Docs](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [next-themes](https://github.com/pacocoursey/next-themes)
