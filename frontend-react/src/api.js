const BASE = '/api'

export async function fetchHealth() {
  const res = await fetch(`${BASE}/health`)
  if (!res.ok) throw new Error('Backend nicht erreichbar')
  return res.json()
}

export async function fetchCollections() {
  const res = await fetch(`${BASE}/collections`)
  if (!res.ok) throw new Error('Sammlungen konnten nicht geladen werden')
  return res.json()
}

export async function deleteCollection(name) {
  const res = await fetch(`${BASE}/collections/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error('Löschen fehlgeschlagen')
  return res.json()
}

export async function uploadPDF(fileBytes, filename, collectionName) {
  const form = new FormData()
  form.append('file', new Blob([fileBytes], { type: 'application/pdf' }), filename)
  if (collectionName) form.append('collection_name', collectionName)

  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
  return data
}

export async function chat(query, agentType, collectionName) {
  const payload = { query, agent_type: agentType }
  if (collectionName) payload.collection_name = collectionName

  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
  return data
}
