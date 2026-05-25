import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getBook } from '../services/api'
import PdfViewer from '../components/PdfViewer'
import { ArrowLeft, BookOpen, Calendar, Building, FileText, Loader2 } from 'lucide-react'

export default function BookDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [book, setBook] = useState(null)
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)

  useEffect(() => {
    getBook(id)
      .then(setBook)
      .catch(() => setBook(null))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div className="flex justify-center mt-16">
      <Loader2 className="animate-spin text-amber-600" size={32} />
    </div>
  )

  if (!book) return (
    <div className="text-center mt-16 text-stone-400">
      <p>Book not found.</p>
      <Link to="/books" className="text-amber-700 hover:underline mt-2 block">← Back to Library</Link>
    </div>
  )

  return (
    <div>
      <Link to="/books" className="flex items-center gap-1 text-sm text-amber-700 hover:underline mb-4">
        <ArrowLeft size={14} /> Back to Library
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Metadata panel */}
        <div className="bg-white border border-stone-200 rounded-xl p-6 h-fit">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-14 bg-amber-100 rounded flex items-center justify-center">
              <BookOpen size={24} className="text-amber-700" />
            </div>
            <div>
              <h1 className="font-['Playfair_Display'] font-bold text-stone-800 text-lg leading-tight">
                {book.title}
              </h1>
            </div>
          </div>

          <dl className="space-y-2 text-sm">
            {[
              { icon: <BookOpen size={13}/>, label: 'Author', value: book.author },
              { icon: <Calendar size={13}/>, label: 'Year', value: book.year },
              { icon: <Building size={13}/>, label: 'Publisher', value: book.publisher },
              { icon: <FileText size={13}/>, label: 'Language', value: book.language },
              { icon: <FileText size={13}/>, label: 'Pages', value: book.max_page },
              { icon: <FileText size={13}/>, label: 'Paragraphs', value: book.paragraph_count?.toLocaleString() },
            ].map(({ icon, label, value }) => value ? (
              <div key={label} className="flex gap-2">
                <span className="text-stone-400 mt-0.5">{icon}</span>
                <div>
                  <span className="text-stone-400 mr-1">{label}:</span>
                  <span className="text-stone-700">{value}</span>
                </div>
              </div>
            ) : null)}
          </dl>

          <button
            onClick={() => navigate(`/?doc_id=${encodeURIComponent(id)}&q=`)}
            className="mt-4 w-full block text-center py-2 bg-amber-700 hover:bg-amber-800
                       text-white rounded-lg text-sm transition-colors">
            Search in this book
          </button>
        </div>

        {/* PDF Viewer */}
        <div className="lg:col-span-2 h-[80vh]">
          <PdfViewer
            docId={id}
            initialPage={currentPage}
          />
        </div>
      </div>
    </div>
  )
}
