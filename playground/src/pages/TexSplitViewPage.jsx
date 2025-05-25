import React, { useState, useEffect, useRef } from 'react'
import SplitPane from 'react-split-pane'
import TexSnipEditor from './TexSnipEditor'
import TexSnipTablePage from './TexSnipTablePage'
import axios from 'axios'

const TexSplitViewPage = () => {
  const [projectName, setProjectName] = useState("")
  const [availableSnapshots, setAvailableSnapshots] = useState([])
  const [splitState, setSplitState] = useState(null)

  const [snipMeta, setSnipMeta] = useState({})
  const [tableMeta, setTableMeta] = useState({})
  const [units, setUnits] = useState([])

  const editorRef = useRef(null)

  const refreshSnapshots = async () => {
    try {
      const res = await axios.get("http://localhost:8000/snip-projects")
      setAvailableSnapshots(Object.keys(res.data))
    } catch (err) {
      console.error("❌ Fehler beim Aktualisieren der Snapshot-Liste:", err)
    }
  }

  useEffect(() => {
    refreshSnapshots()
  }, [])

  useEffect(() => {
    window.onNewUnit = (unit) => {
      console.log("📥 Neue Unit empfangen:", unit)
      setUnits(prev => [...prev, unit])
    }
  }, [])

  const saveCurrentSnapshot = async () => {
    if (!projectName) return alert("Bitte Projektnamen eingeben")
    try {
      const state = {
        sourceFile: snipMeta?.selectedProject || "",
        snipMeta,
        tableMeta
      }
      await axios.post("http://localhost:8000/save-snip-project", {
        project_name: projectName,
        data: state
      })
      await refreshSnapshots()
      alert("✅ Snapshot gespeichert.")
    } catch (err) {
      console.error("❌ Fehler beim Speichern", err)
    }
  }

  const loadSnapshot = async (name) => {
    try {
      const res = await axios.post("http://localhost:8000/load-snip-project", {
        project_name: name
      })
      setSplitState(res.data)
      setProjectName(name)
  
      const sourceFile = res.data?.sourceFile?.split("/")?.[0] || ""
      if (sourceFile) {
        const unitRes = await axios.get(`http://localhost:8000/load-library?source=${sourceFile}`)
        setUnits(unitRes.data)
      }
    } catch (err) {
      console.error("❌ Fehler beim Laden", err)
    }
  }
  

  const handleScrollToUnit = ({ unitID }) => {
    if (editorRef.current?.scrollToUnit) {
      editorRef.current.scrollToUnit(unitID)
    }
  }

  return (
    <div style={{ height: '100vh', width: '100vw' }}>
      {/* Projektleiste */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        padding: '0.5rem 1rem',
        background: '#111',
        borderBottom: '1px solid #444',
        alignItems: 'center'
      }}>
        <input
          placeholder="Projektname"
          value={projectName}
          onChange={e => setProjectName(e.target.value)}
          style={{ padding: "0.3rem", flex: "0 0 200px", fontSize: "0.85rem" }}
        />
        <button onClick={saveCurrentSnapshot} style={{ fontSize: "0.75rem", padding: "0.3rem 0.7rem" }}>
          💾 Snapshot speichern
        </button>
        <select
          onChange={e => loadSnapshot(e.target.value)}
          value={projectName}
          style={{ fontSize: "0.75rem", padding: "0.3rem" }}
        >
          <option value="" disabled hidden>Snapshot laden …</option>
          {availableSnapshots.map(name => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
      </div>

      {/* Split View */}
      <SplitPane
        split="vertical"
        minSize={300}
        defaultSize="55%"
        style={{ position: 'relative' }}
      >
        <div style={{ height: '100%', overflow: 'auto' }}>
        <TexSnipEditor
            ref={editorRef}
            splitState={splitState}
            onMetaChange={setSnipMeta}
            onNewUnit={(unit) => {
                console.log("📥 Neue Unit empfangen:", unit)
                setUnits(prev => [...prev, unit])
            }}
        />
        </div>
        <div style={{ height: '100%', overflow: 'auto', padding: '1rem' }}>
          <TexSnipTablePage
            units={units}
            splitState={splitState}
            onMetaChange={setTableMeta}
            onJumpToUnit={handleScrollToUnit}
          />
        </div>
      </SplitPane>
    </div>
  )
}

export default TexSplitViewPage
