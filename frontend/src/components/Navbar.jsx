import { Link, useLocation } from 'react-router-dom'
import { BookOpen, Search } from 'lucide-react'

export default function Navbar() {
  const loc = useLocation()
  const active = (path) => loc.pathname === path
    ? 'text-amber-700 border-b-2 border-amber-700'
    : 'text-stone-600 hover:text-amber-700'

  return (
    <nav className="bg-stone-800 text-amber-50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-8">
        <a href="/" className="flex items-center gap-2 font-['Playfair_Display'] text-xl font-bold text-amber-300">
          <BookOpen size={24} />
          BookSearch
        </a>
        <div className="flex gap-6 ml-auto">
          <a href="/" className={`flex items-center gap-1 pb-1 transition-colors ${active('/')}`}>
            <Search size={16}/> Search
          </a>
          <Link to="/books" className={`flex items-center gap-1 pb-1 transition-colors ${active('/books')}`}>
            <BookOpen size={16}/> Library
          </Link>
        </div>
      </div>
    </nav>
  )
}
