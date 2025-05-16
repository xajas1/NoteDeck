import Sidebar from './components/Sidebar'
import { useState, useEffect } from 'react'
import PlaygroundList from './components/PlaygroundList' // ✅ Drag-and-Drop-Version verwenden
import PlaygroundGrouped from './components/PlaygroundGrouped'

function App() {
  const [units, setUnits] = useState([])
  const [loading, setLoading] = useState(true)
  const [playground, setPlayground] = useState([])

  useEffect(() => {
    fetch('http://127.0.0.1:8000/units')
      .then(res => res.json())
      .then(data => {
        console.log("📦 Loaded units:", data)
        setUnits(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Fehler beim Laden der Units:', err)
        setLoading(false)
      })
  }, [])

  const addToPlayground = (unit) => {
    if (!playground.some(entry => entry.UnitID === unit.UnitID)) {
      setPlayground([...playground, {
        UnitID: unit.UnitID,
        Section: "1",
        Subsection: "1.1",
        Order: playground.length + 1
      }])
    }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Linke Seitenleiste */}
      <Sidebar units={units} playground={playground} setPlayground={setPlayground} />

      {/* Hauptinhalt */}
      <div style={{ flex: 1, padding: '2rem', backgroundColor: '#1a1a1a', color: '#eee', overflowY: 'auto' }}>
        <h1>📚 NoteDeck Playground</h1>
        <p>Anzahl geladener Einheiten: {units.length}</p>

        {loading ? (
          <p>⏳ Lade Inhalte …</p>
        ) : (
          <PlaygroundGrouped playground={playground} setPlayground={setPlayground} />
        )}
      </div>
    </div>
  )
}

export default App
