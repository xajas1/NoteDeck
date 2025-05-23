import React, { useEffect, useState } from 'react'
import axios from 'axios'
import TexSnipTable from '../components/TexSnipTable'

const TexSnipTablePage = ({ splitState, onMetaChange }) => {
  const [sources, setSources] = useState([])
  const [selectedSource, setSelectedSource] = useState("")
  const [units, setUnits] = useState([])

  // Quellen laden
  useEffect(() => {
    axios.get('http://localhost:8000/available-sources')
      .then(res => {
        console.log("🧾 Quellen geladen:", res.data)
        setSources(res.data)
      })
      .catch(err => console.error("❌ Fehler beim Laden der Quellen:", err))
  }, [])

  // Units laden bei Quellenauswahl
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

  // Bei geladenem Snapshot: Quelle übernehmen
  useEffect(() => {
    if (splitState?.tableMeta?.SelectedSource) {
      setSelectedSource(splitState.tableMeta.SelectedSource)
    }
  }, [splitState])

  // Metadaten zurückmelden
  useEffect(() => {
    if (onMetaChange) {
      onMetaChange({
        SelectedSource: selectedSource
      })
    }
  }, [selectedSource])

  return (
    <div style={{ padding: "0.5rem", fontSize: "0.85rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <label htmlFor="source-select" style={{ fontWeight: 500 }}>Quelle:</label>
        <select
          id="source-select"
          value={selectedSource}
          onChange={e => setSelectedSource(e.target.value)}
        >
          <option value="">-- Quelle wählen --</option>
          {sources.map(src => (
            <option key={src} value={src}>{src}</option>
          ))}
        </select>
        <span style={{ color: "#888", fontSize: "0.75rem" }}>
          {selectedSource && `(${units.length} Units geladen)`}
        </span>
      </div>

      <TexSnipTable units={units} />
    </div>
  )
}

export default TexSnipTablePage
