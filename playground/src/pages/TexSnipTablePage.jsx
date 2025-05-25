import React, { useEffect, useState } from 'react'
import axios from 'axios'
import TexSnipTable from '../components/TexSnipTable'

const TexSnipTablePage = ({ splitState, onMetaChange, onJumpToUnit }) => {
  const [sources, setSources] = useState([])
  const [selectedSource, setSelectedSource] = useState("")
  const [units, setUnits] = useState([])
  const [sourceMap, setSourceMap] = useState({})

  // SourceMap laden
  useEffect(() => {
    axios.get("http://localhost:8000/source-map")
      .then(res => setSourceMap(res.data))
      .catch(err => console.error("❌ Fehler beim Laden der SourceMap:", err))
  }, [])

  // Quellenliste für Dropdown laden
  useEffect(() => {
    axios.get("http://localhost:8000/available-sources")
      .then(res => setSources(res.data))
      .catch(err => console.error("❌ Fehler beim Laden der Quellenliste:", err))
  }, [])

  // Snapshot-Einstellungen anwenden
  useEffect(() => {
    if (splitState?.tableMeta?.selectedSource) {
      setSelectedSource(splitState.tableMeta.selectedSource)
    } else if (splitState?.sourceFile) {
      setSelectedSource(splitState.sourceFile)
    }
  }, [splitState])

  // Units laden bei Quellenauswahl
  useEffect(() => {
    if (selectedSource) {
      axios.get(`http://localhost:8000/load-library?source=${selectedSource}`)
        .then(res => setUnits(res.data))
        .catch(err => console.error("❌ Fehler beim Laden der Units:", err))
    }
  }, [selectedSource])

  // tableMeta zurückgeben
  useEffect(() => {
    if (onMetaChange) {
      onMetaChange({ selectedSource })
    }
  }, [selectedSource])

  // Neue Units per window.onNewUnit
  useEffect(() => {
    const handler = (unit) => {
      console.log("📥 Neue Unit empfangen:", unit)
      const litID = sourceMap[selectedSource]
      console.log("🔍 Vergleich:", unit.LitID, "vs.", litID)

      if (unit.LitID === litID) {
        setUnits(prev => [...prev, unit])
        console.log("✅ Neue Unit zur Tabelle hinzugefügt:", unit)
      } else {
        console.warn("⚠️ Neue Unit gehört nicht zur aktuellen Quelle – wird nicht angezeigt")
      }
    }

    window.onNewUnit = handler

    return () => {
      if (window.onNewUnit === handler) {
        window.onNewUnit = null
      }
    }
  }, [selectedSource, sourceMap])

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

      <TexSnipTable
        units={units}
        onJumpToUnit={onJumpToUnit}
      />
    </div>
  )
}

export default TexSnipTablePage
