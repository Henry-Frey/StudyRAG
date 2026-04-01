export default function StatusBar({ health, collections }) {
  const totalDocs = collections.reduce((sum, c) => sum + (c.document_count ?? 0), 0)
  const online = health !== null

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginTop: 10,
      padding: '0 2px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <div style={{
          width: 6, height: 6,
          borderRadius: '50%',
          background: online ? 'var(--success)' : '#EF4444',
          flexShrink: 0,
        }} />
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {online
            ? `${totalDocs} Dokumente · ${collections.length} Sammlungen`
            : 'Backend nicht erreichbar'}
        </span>
      </div>
      {health && (
        <span style={{
          fontSize: 10,
          color: health.llm_loaded ? 'var(--text-muted)' : '#F97316',
          fontWeight: 500,
        }}>
          {health.llm_loaded ? 'LLM OK' : 'LLM ausstehend'}
        </span>
      )}
    </div>
  )
}
