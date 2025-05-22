// playground/src/pages/TexEditorPage.jsx
import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { useNavigate } from 'react-router-dom'

export default function TexEditorPage() {
  const navigate = useNavigate()

  const [code, setCode] = useState(String.raw`
\documentclass{article}
\begin{document}
Hello World!
\end{document}
  `)

  const [pdfUrl, setPdfUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const compileLatex = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('http://localhost:8000/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tex: code })
      })

      if (!res.ok) throw new Error(await res.text())

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      setPdfUrl(url)
    } catch (e) {
      console.error(e)
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSnip = () => {
    alert('🧠 Snip-Aktion wird hier ausgeführt')
  }

  const handleKeyDown = (e) => {
    const isMac = navigator.platform.includes('Mac')
    if ((isMac ? e.metaKey : e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSnip()
    }
  }

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      display: 'flex',
      flexDirection: 'row',
      backgroundColor: '#1a1a1a',
      color: '#eee',
      overflow: 'hidden'
    }}>
      {/* Editor Panel */}
      <div style={{ flex: 3, display: 'flex', flexDirection: 'column', borderRight: '1px solid #333' }}>
        <div style={{ padding: '0.5rem 1rem', background: '#111', display: 'flex', justifyContent: 'space-between' }}>
          <h2 style={{ margin: 0 }}>✂️ TeX Snip Editor</h2>
          <button onClick={() => navigate('/')} style={styles.buttonDark}>← Zurück</button>
        </div>
        <div style={{ flexGrow: 1 }}>
          <Editor
            height="100%"
            defaultLanguage="latex"
            value={code}
            onChange={value => setCode(value)}
            theme="vs-dark"
          />
        </div>
        <div style={{ padding: '0.5rem 1rem', background: '#111', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
          <button onClick={compileLatex} style={styles.buttonGreen}>🧪 Kompilieren</button>
          <button onClick={handleSnip} style={styles.buttonBlue}>✂️ Snip</button>
          {error && <p style={{ color: 'red', marginLeft: '1rem' }}>{error}</p>}
        </div>
      </div>

      {/* PDF Preview Panel via iframe */}
      <div style={{ flex: 2, display: 'flex', flexDirection: 'column', background: '#222' }}>
        <div style={{ padding: '0.5rem 1rem', background: '#111' }}>
          <h3 style={{ margin: 0 }}>📄 PDF Vorschau</h3>
        </div>
        <div style={{ flexGrow: 1, overflow: 'hidden' }}>
          {loading && <p style={{ padding: '1rem' }}>⏳ Kompiliere…</p>}
          {pdfUrl && (
            <iframe
              src={pdfUrl}
              title="PDF Vorschau"
              width="100%"
              height="100%"
              style={{ border: 'none' }}
            />
          )}
        </div>
      </div>
    </div>
  )
}

const styles = {
  buttonDark: {
    background: '#333',
    color: '#eee',
    padding: '0.3rem 0.8rem',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.75rem',
    cursor: 'pointer'
  },
  buttonGreen: {
    background: '#4a4',
    color: 'white',
    padding: '0.4rem 0.8rem',
    fontSize: '0.8rem',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer'
  },
  buttonBlue: {
    background: '#2299dd',
    color: 'white',
    padding: '0.4rem 0.8rem',
    fontSize: '0.8rem',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer'
  }
}
