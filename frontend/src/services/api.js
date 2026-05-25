import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const searchParagraphs = (params) =>
  api.get('/search/', { params }).then(r => r.data)

export const getSuggestions = (q) =>
  api.get('/search/suggest', { params: { q } }).then(r => r.data)

export const listBooks = (params) =>
  api.get('/metadata/books', { params }).then(r => r.data)

export const getBook = (docId) =>
  api.get(`/metadata/books/${docId}`).then(r => r.data)

export const getPdfPageUrl = (docId, pageNumber, zoom = 1.5, highlightWord = '') =>
  `/api/pdf/${docId}/page/${pageNumber}?zoom=${zoom}${highlightWord ? '&highlight=' + encodeURIComponent(highlightWord) : ''}`

export const getPdfInfo = (docId) =>
  api.get(`/pdf/${docId}/info`).then(r => r.data)
