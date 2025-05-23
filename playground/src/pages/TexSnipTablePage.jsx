import React, { useEffect, useState } from 'react'
import axios from 'axios'
import TexSnipTable from '../components/TexSnipTable'

const TexSnipTablePage = () => {
  const [sources, setSources] = useState([])
  const [selectedSource, setSelectedSource] = useState("")
  const [units, setUnits] = useState([])

  // Lade Quellen
  useEffect(() => {
    axios.get('http://localhost:8000/available-sources')
      .then(res => {
        console.log("🧾 Quellen geladen:", res.data)
        setSources(res.data)
      })
      .catch(err => console.error("❌ Fehler beim Laden der Quellen:", err))
  }, [])

  // Lade Units, wenn Quelle ausgewählt wurde
  useEffect(() => {
    if (selectedSource) {
      console.log("📡 Lade Units für:", selectedSource)
      axios.get(`http://localhost:8000/load-library?source=${selectedSource}`)
        .then(res => {
          console.log("📥 Units erhalten:", res.data)
          setUnits(res.data)
        })
        .catch(err => console.error("❌ Fehler beim Laden der Units:", err))
    }
  }, [selectedSource])

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Tex Snip Table</h1>

      <label htmlFor="source-select">Wähle eine Quelle:</label>
      <select
        id="source-select"
        value={selectedSource}
        onChange={e => setSelectedSource(e.target.value)}
        style={{ marginLeft: "1rem" }}
      >
        <option value="">-- Quelle wählen --</option>
        {sources.map(src => (
          <option key={src} value={src}>{src}</option>
        ))}
      </select>

      {selectedSource && (
        <p style={{ marginTop: "1rem" }}>
          {units.length} Units geladen für <strong>{selectedSource}</strong>.
        </p>
      )}

      <TexSnipTable units={units} />
    </div>
  )
}

export default TexSnipTablePage
