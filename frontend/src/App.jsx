import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import SearchPage from './pages/SearchPage'
import BooksPage from './pages/BooksPage'
import BookDetailPage from './pages/BookDetailPage'

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/"          element={<SearchPage />} />
          <Route path="/books"     element={<BooksPage />} />
          <Route path="/books/:id" element={<BookDetailPage />} />
        </Routes>
      </main>
    </div>
  )
}
