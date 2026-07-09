import { useEffect, useRef, useState } from 'react'
import { getJobStatus, cancelJob } from '../api.js'

export default function JobProgress({ jobId, onComplete, onReset }) {
  const [job, setJob] = useState(null)
  const [error, setError] = useState('')
  const timer = useRef(null)

  useEffect(() => {
    let active = true

    async function poll() {
      try {
        const data = await getJobStatus(jobId)
        if (!active) return
        setJob(data)
        if (data.status === 'SUCCESS') {
          onComplete()
          return
        }
        if (data.status === 'FAILED' || data.status === 'CANCELLED') {
          return
        }
        timer.current = setTimeout(poll, 2000)
      } catch (err) {
        if (active) setError(err.message)
      }
    }

    poll()
    return () => {
      active = false
      if (timer.current) clearTimeout(timer.current)
    }
  }, [jobId, onComplete])

  async function handleCancel() {
    try {
      await cancelJob(jobId)
    } catch (err) {
      setError(err.message)
    }
  }

  const status = job?.status || 'QUEUED'
  const progress = job?.progress || 0

  return (
    <div className="card">
      <h2>Processing job</h2>
      <p className="muted mono">{jobId}</p>

      <div className="status-row">
        <span className={`badge ${status.toLowerCase()}`}>{status}</span>
        <span>{progress}%</span>
      </div>

      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      {job?.regex_pattern && (
        <p className="muted">
          Generated regex: <code>{job.regex_pattern}</code>
        </p>
      )}

      {status === 'FAILED' && <p className="error">{job?.error_message || 'Job failed.'}</p>}
      {status === 'CANCELLED' && <p className="error">Job was cancelled.</p>}
      {error && <p className="error">{error}</p>}

      <div className="actions">
        {(status === 'QUEUED' || status === 'RUNNING') && (
          <button className="btn" onClick={handleCancel}>
            Cancel job
          </button>
        )}
        {(status === 'FAILED' || status === 'CANCELLED') && (
          <button className="btn primary" onClick={onReset}>
            Start over
          </button>
        )}
      </div>
    </div>
  )
}
