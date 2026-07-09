import { useState } from 'react'
import { fetchColumns, createJob } from '../api.js'

export default function UploadForm({ onJobCreated }) {
  const [file, setFile] = useState(null)
  const [columns, setColumns] = useState([])
  const [selectedColumns, setSelectedColumns] = useState([])
  const [prompt, setPrompt] = useState('')
  const [replacement, setReplacement] = useState('')
  const [loadingColumns, setLoadingColumns] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleFileChange(e) {
    const selected = e.target.files[0]
    if (!selected) return
    setFile(selected)
    setColumns([])
    setSelectedColumns([])
    setError('')
    setLoadingColumns(true)
    try {
      const data = await fetchColumns(selected)
      setColumns(data.columns)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingColumns(false)
    }
  }

  function toggleColumn(col) {
    setSelectedColumns((prev) =>
      prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]
    )
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!file) return setError('Please choose a file.')
    if (selectedColumns.length === 0) return setError('Select at least one column.')
    if (!prompt.trim()) return setError('Describe the pattern to match.')

    setSubmitting(true)
    try {
      const { job_id } = await createJob({
        file,
        prompt,
        replacement,
        columns: selectedColumns,
      })
      onJobCreated(job_id)
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <label className="field">
        <span>Upload CSV or Excel file</span>
        <input type="file" accept=".csv,.xls,.xlsx" onChange={handleFileChange} />
      </label>

      {loadingColumns && <p className="muted">Reading columns…</p>}

      {columns.length > 0 && (
        <div className="field">
          <span>Target columns</span>
          <div className="chips">
            {columns.map((col) => (
              <button
                type="button"
                key={col}
                className={selectedColumns.includes(col) ? 'chip active' : 'chip'}
                onClick={() => toggleColumn(col)}
              >
                {col}
              </button>
            ))}
          </div>
        </div>
      )}

      <label className="field">
        <span>Describe the pattern</span>
        <input
          type="text"
          placeholder="e.g. find email addresses"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
      </label>

      <label className="field">
        <span>Replacement value</span>
        <input
          type="text"
          placeholder="e.g. REDACTED"
          value={replacement}
          onChange={(e) => setReplacement(e.target.value)}
        />
      </label>

      {error && <p className="error">{error}</p>}

      <button className="btn primary" type="submit" disabled={submitting}>
        {submitting ? 'Starting…' : 'Run replacement'}
      </button>
    </form>
  )
}
