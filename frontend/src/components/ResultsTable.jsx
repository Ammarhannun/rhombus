import { useEffect, useState } from 'react'
import { getJobResults } from '../api.js'

export default function ResultsTable({ jobId, onReset }) {
  const [data, setData] = useState(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    getJobResults(jobId, page)
      .then((res) => {
        if (active) setData(res)
      })
      .catch((err) => {
        if (active) setError(err.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [jobId, page])

  if (error) {
    return (
      <div className="card">
        <p className="error">{error}</p>
        <button className="btn primary" onClick={onReset}>Start over</button>
      </div>
    )
  }

  if (!data) {
    return <div className="card"><p className="muted">Loading results…</p></div>
  }

  return (
    <div className="card">
      <div className="results-head">
        <h2>Processed data</h2>
        <span className="muted">{data.total_rows.toLocaleString()} rows</span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {data.columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, i) => (
              <tr key={i}>
                {data.columns.map((col) => (
                  <td key={col}>{String(row[col] ?? '')}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <button className="btn" disabled={page <= 1 || loading} onClick={() => setPage((p) => p - 1)}>
          Previous
        </button>
        <span>
          Page {data.page} of {data.total_pages}
        </span>
        <button
          className="btn"
          disabled={page >= data.total_pages || loading}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>

      <div className="actions">
        <button className="btn primary" onClick={onReset}>Process another file</button>
      </div>
    </div>
  )
}
