import { useEffect, useState, useMemo } from 'react'

const fmt = (n) => n == null ? '—' : `$${Number(n).toLocaleString()}`

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [sort, setSort] = useState('expected_clearing')
  const [minScarcity, setMinScarcity] = useState(70)
  const [parkingOnly, setParkingOnly] = useState(false)

  useEffect(() => {
    fetch('./data/listings.json')
      .then((r) => {
        if (!r.ok) throw new Error('No data file yet — run the sweep at least once.')
        return r.json()
      })
      .then(setData)
      .catch((e) => setError(e.message))
  }, [])

  const filtered = useMemo(() => {
    if (!data) return []
    let rows = data.listings.filter((r) => r.scarcity >= minScarcity)
    if (parkingOnly) rows = rows.filter((r) => (r.parking || 0) > 0)
    rows = rows.slice().sort((a, b) => {
      if (sort === 'expected_clearing') return a.expected_clearing - b.expected_clearing
      if (sort === 'scarcity') return b.scarcity - a.scarcity
      return 0
    })
    return rows
  }, [data, minScarcity, parkingOnly, sort])

  if (error) {
    return (
      <div style={{ padding: 24, fontFamily: 'system-ui' }}>
        <h2>Property Scanner</h2>
        <p style={{ color: '#b45309' }}>{error}</p>
        <p>Trigger the workflow once from the Actions tab, or wait for the next scheduled run.</p>
      </div>
    )
  }

  if (!data) {
    return <div style={{ padding: 24, fontFamily: 'system-ui' }}>Loading…</div>
  }

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui', maxWidth: 900, margin: '0 auto' }}>
      <h2 style={{ marginBottom: 4 }}>Property Scanner</h2>
      <p style={{ color: '#666', marginTop: 0 }}>
        {data.count} matches · cap {fmt(data.brief.expected_price_cap)} · last swept{' '}
        {new Date(data.generated_at).toLocaleString()}
      </p>

      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
        <label>
          Sort:{' '}
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="expected_clearing">Price (low to high)</option>
            <option value="scarcity">Scarcity (high to low)</option>
          </select>
        </label>
        <label>
          Min scarcity:{' '}
          <input
            type="number" min={0} max={100} value={minScarcity}
            onChange={(e) => setMinScarcity(Number(e.target.value))}
            style={{ width: 56 }}
          />
        </label>
        <label>
          <input type="checkbox" checked={parkingOnly} onChange={(e) => setParkingOnly(e.target.checked)} />
          {' '}Parking only
        </label>
      </div>

      {filtered.length === 0 && <p>No listings match these filters right now.</p>}

      <div style={{ display: 'grid', gap: 12 }}>
        {filtered.map((r) => (
          <a
            key={r.id}
            href={r.url}
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'block', padding: 16, border: '1px solid #e5e5e5', borderRadius: 8,
              textDecoration: 'none', color: 'inherit',
            }}
          >
            <div style={{ fontWeight: 600 }}>{r.address}</div>
            <div style={{ color: '#666', fontSize: 14, marginTop: 4 }}>
              {r.beds} bed · {r.baths} bath · {r.parking || 0} car · {r.method === 'auction' ? 'auction' : 'private treaty'}
            </div>
            <div style={{ marginTop: 8, display: 'flex', gap: 16, fontSize: 14 }}>
              <span>Guide {fmt(r.guide_price)}</span>
              <span>Expected {fmt(r.expected_clearing)}</span>
              <span>Scarcity {r.scarcity}</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}
