import { useState } from 'react'
import UploadForm from './components/UploadForm.jsx'
import JobProgress from './components/JobProgress.jsx'
import ResultsTable from './components/ResultsTable.jsx'

export default function App() {
  const [stage, setStage] = useState('upload')
  const [jobId, setJobId] = useState(null)

  function handleJobCreated(id) {
    setJobId(id)
    setStage('progress')
  }

  function handleComplete() {
    setStage('results')
  }

  function reset() {
    setJobId(null)
    setStage('upload')
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Rhombus</h1>
        <p>Natural language pattern matching and replacement at scale</p>
      </header>

      <main className="main">
        {stage === 'upload' && <UploadForm onJobCreated={handleJobCreated} />}
        {stage === 'progress' && (
          <JobProgress jobId={jobId} onComplete={handleComplete} onReset={reset} />
        )}
        {stage === 'results' && <ResultsTable jobId={jobId} onReset={reset} />}
      </main>
    </div>
  )
}
