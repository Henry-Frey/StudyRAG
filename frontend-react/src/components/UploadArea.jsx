import { useState, useRef } from 'react'
import { uploadPDF } from '../api.js'

export default function UploadArea({ onUploadComplete }) {
  const [isDragOver, setIsDragOver]   = useState(false)
  const [collectionName, setCollectionName] = useState('')
  const [pendingFiles, setPendingFiles] = useState([])
  const [uploading, setUploading]     = useState(false)
  const [results, setResults]         = useState([])
  const fileInputRef = useRef(null)

  function handleDragOver(e) {
    e.preventDefault()
    setIsDragOver(true)
  }
  function handleDragLeave() {
    setIsDragOver(false)
  }
  async function handleDrop(e) {
    e.preventDefault()
    setIsDragOver(false)
    const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'))
    if (files.length) addFiles(files)
  }
  function handleFileInput(e) {
    const files = Array.from(e.target.files)
    if (files.length) addFiles(files)
    e.target.value = ''
  }
  async function addFiles(files) {
    const entries = await Promise.all(
      files.map(async f => {
        const bytes = await f.arrayBuffer()
        return { name: f.name, bytes }
      })
    )
    setPendingFiles(prev => [...prev, ...entries])
    setResults([])
  }

  async function handleUpload() {
    if (!pendingFiles.length || uploading) return
    setUploading(true)
    setResults([])
    const newResults = []
    for (const { name, bytes } of pendingFiles) {
      const col = collectionName.trim() || name.replace(/\.pdf$/i, '').replace(/\s+/g, '_')
      try {
        const data = await uploadPDF(bytes, name, col)
        newResults.push({ name, ok: true, chunks: data.chunks_added, pages: data.pages_processed })
      } catch (err) {
        newResults.push({ name, ok: false, error: err.message })
      }
    }
    setResults(newResults)
    setPendingFiles([])
    setUploading(false)
    await onUploadComplete()
  }

  return (
    <div style={{
      background: 'var(--bg-upload)',
      border: '1px solid var(--border)',
      borderRadius: 10,
      padding: 12,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10 }}>
        <UploadIcon />
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
          Dokumente hochladen
        </span>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragOver ? 'var(--primary)' : 'var(--border-dashed)'}`,
          borderRadius: 8,
          padding: '14px 12px',
          textAlign: 'center',
          cursor: 'pointer',
          background: isDragOver ? 'var(--primary-light)' : 'transparent',
          transition: 'border-color 0.15s ease, background 0.15s ease',
          marginBottom: 10,
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileInput}
          style={{ display: 'none' }}
        />
        {pendingFiles.length > 0 ? (
          <div style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 500 }}>
            {pendingFiles.length} Datei{pendingFiles.length > 1 ? 'en' : ''} ausgewählt
          </div>
        ) : (
          <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
            PDF-Dateien hierher ziehen
            <br />
            <span style={{ fontSize: 11 }}>oder klicken zum Auswählen</span>
          </div>
        )}
      </div>

      {/* Collection name + upload button */}
      <div style={{ display: 'flex', gap: 6 }}>
        <input
          type="text"
          placeholder="Sammlungsname"
          value={collectionName}
          onChange={e => setCollectionName(e.target.value)}
          style={{
            flex: 1,
            padding: '6px 9px',
            borderRadius: 6,
            border: '1px solid var(--border)',
            fontSize: 12,
            color: 'var(--text-primary)',
            background: 'var(--white)',
            outline: 'none',
            minWidth: 0,
          }}
        />
        <button
          onClick={handleUpload}
          disabled={!pendingFiles.length || uploading}
          style={{
            padding: '6px 12px',
            borderRadius: 6,
            border: 'none',
            background: (!pendingFiles.length || uploading) ? 'var(--text-muted)' : 'var(--primary)',
            color: 'white',
            fontSize: 12,
            fontWeight: 600,
            cursor: (!pendingFiles.length || uploading) ? 'not-allowed' : 'pointer',
            whiteSpace: 'nowrap',
            transition: 'background 0.15s ease',
          }}
        >
          {uploading ? '...' : 'Hochladen'}
        </button>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {results.map((r, i) => (
            <div key={i} style={{
              fontSize: 11,
              padding: '4px 8px',
              borderRadius: 5,
              background: r.ok ? '#F0FDF4' : '#FEF2F2',
              color: r.ok ? '#166534' : '#991B1B',
            }}>
              {r.ok
                ? `${r.name}: ${r.chunks} Chunks, ${r.pages} Seiten`
                : `${r.name}: ${r.error}`}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function UploadIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  )
}
