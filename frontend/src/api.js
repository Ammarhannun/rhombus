const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export async function fetchColumns(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_URL}/columns/`, { method: 'POST', body: form })
  if (!res.ok) throw new Error((await res.json()).error || 'Failed to read columns')
  return res.json()
}

export async function createJob({ file, prompt, replacement, columns }) {
  const form = new FormData()
  form.append('input_file', file)
  form.append('original_filename', file.name)
  form.append('nl_prompt', prompt)
  form.append('replacement_value', replacement)
  columns.forEach((c) => form.append('target_columns', c))
  const res = await fetch(`${API_URL}/jobs/`, { method: 'POST', body: form })
  if (!res.ok) throw new Error((await res.json()).error || 'Failed to create job')
  return res.json()
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${API_URL}/jobs/${jobId}/`)
  if (!res.ok) throw new Error('Failed to fetch job status')
  return res.json()
}

export async function getJobResults(jobId, page = 1, pageSize = 100) {
  const res = await fetch(`${API_URL}/jobs/${jobId}/results/?page=${page}&page_size=${pageSize}`)
  if (!res.ok) throw new Error('Failed to fetch results')
  return res.json()
}

export async function cancelJob(jobId) {
  const res = await fetch(`${API_URL}/jobs/${jobId}/cancel/`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to cancel job')
  return res.json()
}
