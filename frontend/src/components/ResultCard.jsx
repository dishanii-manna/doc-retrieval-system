import { BookOpen, FileText, Calendar, Building } from 'lucide-react'

export default function ResultCard({ result, onSelect, isSelected }) {
  return (
    <div
      onClick={() => onSelect(result)}
      className={`cursor-pointer rounded-xl border-2 p-5 transition-all hover:shadow-md
        ${isSelected
          ? 'border-amber-500 bg-amber-50 shadow-md'
          : 'border-stone-200 bg-white hover:border-amber-300'
        }`}
    >
      {/* Book info */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="font-['Playfair_Display'] font-semibold text-stone-800 text-lg leading-tight">
            {result.book_title || result.doc_id}
          </h3>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-sm text-stone-500">
            {result.author && (
              <span className="flex items-center gap-1">
                <BookOpen size={13} /> {result.author}
              </span>
            )}
            {result.year && (
              <span className="flex items-center gap-1">
                <Calendar size={13} /> {result.year}
              </span>
            )}
            {result.publisher && (
              <span className="flex items-center gap-1">
                <Building size={13} /> {result.publisher}
              </span>
            )}
          </div>
        </div>
        <span className="shrink-0 text-xs bg-stone-100 text-stone-600 px-2 py-1 rounded-lg flex items-center gap-1">
          <FileText size={12} /> Page {result.page_number}
        </span>
      </div>

      {/* Highlighted excerpt */}
      <p
        className="text-stone-700 text-sm leading-relaxed line-clamp-4 font-['Source_Serif_4']"
        dangerouslySetInnerHTML={{
          __html: result.highlight || result.text.slice(0, 400) + '…'
        }}
      />

      <div className="mt-3 flex items-center gap-2 text-xs text-amber-700">
        <span className="bg-amber-100 px-2 py-0.5 rounded">
          Relevance: {(result.score).toFixed(2)}
        </span>
        <span className="text-stone-400">Click to view PDF page →</span>
      </div>
    </div>
  )
}
