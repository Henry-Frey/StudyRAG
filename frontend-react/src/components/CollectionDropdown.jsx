export default function CollectionDropdown({ collections, selected, onChange }) {
  return (
    <div>
      <div style={labelStyle}>SAMMLUNG</div>
      <select
        value={selected ?? ''}
        onChange={e => onChange(e.target.value || null)}
        style={{
          width: '100%',
          padding: '8px 10px',
          borderRadius: 8,
          border: '1px solid var(--border)',
          fontSize: 13,
          color: 'var(--text-secondary)',
          background: 'var(--white)',
          cursor: 'pointer',
          outline: 'none',
          appearance: 'none',
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 10px center',
          paddingRight: 30,
        }}
      >
        <option value="">Alle Sammlungen</option>
        {collections.map(c => (
          <option key={c.name} value={c.name}>{c.name}</option>
        ))}
      </select>
    </div>
  )
}

const labelStyle = {
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: '0.8px',
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
  marginBottom: 6,
}
