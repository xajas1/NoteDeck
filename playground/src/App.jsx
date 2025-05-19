import { useEffect, useState } from 'react'
import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'

import TreePlaygroundView from './components/TreePlaygroundView'
import TreeEditorView from './components/TreeEditorView'
import TreeSidebar from './components/TreeSidebar'

function App() {
  const [units, setUnits] = useState([])
  const [loading, setLoading] = useState(true)
  const [playground, setPlayground] = useState([])
  const [structure, setStructure] = useState([])

  const [selectedPlaygroundIDs, setSelectedPlaygroundIDs] = useState(new Set())
  const [selectedEditorIDs, setSelectedEditorIDs] = useState(new Set())
  const [lastSelectedPlaygroundIndex, setLastSelectedPlaygroundIndex] = useState(null)
  const [lastSelectedEditorIndex, setLastSelectedEditorIndex] = useState(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    })
  )

  const STORAGE_KEY = "notedeck_playground_v1"

  const saveStructureToLocal = () => {
    if (!structure || structure.length === 0) {
      alert("⚠️ Keine Struktur vorhanden zum Speichern.")
      return
    }

    const data = {
      structure,
      playground,
      timestamp: Date.now()
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    alert("✅ Struktur gespeichert!")
  }

  const loadStructureFromLocal = () => {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return alert("⚠️ Keine gespeicherte Struktur gefunden.")

    try {
      const parsed = JSON.parse(raw)
      if (parsed.structure && Array.isArray(parsed.structure)) {
        setStructure(parsed.structure)
        setPlayground(parsed.playground || [])
        alert("📂 Struktur erfolgreich geladen.")
      } else {
        alert("❌ Ungültiges Speicherformat.")
      }
    } catch (e) {
      console.error(e)
      alert("❌ Fehler beim Laden.")
    }
  }

  const resetEditorView = () => {
    setStructure([])
    setPlayground([])
    alert("🔄 Editor zurückgesetzt (nicht gespeichert).")
  }

  const deleteSavedStructure = () => {
    localStorage.removeItem(STORAGE_KEY)
    alert("🗑 Lokaler Speicher gelöscht.")
  }

  const normalizeUnitID = (id) => {
    if (id.includes('____drop__')) return id.split('____drop__')[1]
    if (id.includes('__drop__')) return id.split('__drop__')[1]
    if (id.includes('__')) return id.split('__')[1]
    return id
  }

  const handleDragEnd = ({ active, over }) => {
    if (!active || !over || active.id === over.id) return

    const activeType = active.data.current?.type
    const overId = over.id

    if (activeType === 'section') {
      setStructure(prev => {
        const oldIndex = prev.findIndex(s => s.id === active.id)
        const newIndex = prev.findIndex(s => s.id === overId)
        if (oldIndex === -1 || newIndex === -1) return prev

        const updated = [...prev]
        const [moved] = updated.splice(oldIndex, 1)
        updated.splice(newIndex, 0, moved)
        return updated
      })
    }

    else if (activeType === 'subsection') {
      const parentId = active.data.current?.parentId
      setStructure(prev =>
        prev.map(section => {
          if (section.id !== parentId) return section

          const subs = [...section.subsections]
          const oldIndex = subs.findIndex(sub => sub.id === active.id)
          const newIndex = subs.findIndex(sub => sub.id === overId)
          if (oldIndex === -1 || newIndex === -1) return section

          const [moved] = subs.splice(oldIndex, 1)
          subs.splice(newIndex, 0, moved)

          return { ...section, subsections: subs }
        })
      )
    }

    else {
      const draggedIDs =
        active?.data?.current?.draggedIDs ||
        (selectedPlaygroundIDs.size > 0
          ? Array.from(selectedPlaygroundIDs)
          : selectedEditorIDs.size > 0
          ? Array.from(selectedEditorIDs)
          : [normalizeUnitID(active.id)])

      const targetSubID = over.id.includes('__')
        ? over.id.split('__')[0]
        : over.id

      const targetIndexUnit = over.id.includes('__')
        ? normalizeUnitID(over.id)
        : null

      setStructure(prev =>
        prev.map(section => ({
          ...section,
          subsections: section.subsections.map(sub => {
            let current = [...sub.unitIDs]
            const fromIndex = current.indexOf(draggedIDs[0])
            const toIndex = targetIndexUnit ? current.indexOf(targetIndexUnit) : current.length

            if (fromIndex === -1 && sub.id !== targetSubID) {
              return {
                ...sub,
                unitIDs: current.filter(id => !draggedIDs.includes(id))
              }
            }

            let updated = current.filter(id => !draggedIDs.includes(id))
            let insertAt = toIndex
            if (fromIndex < toIndex) {
              insertAt = toIndex - draggedIDs.length + 1
            }

            if (sub.id === targetSubID) {
              draggedIDs.forEach((id, i) => {
                updated.splice(insertAt + i, 0, id)
              })
            }

            return { ...sub, unitIDs: updated }
          })
        }))
      )
    }

    setSelectedPlaygroundIDs(new Set())
    setSelectedEditorIDs(new Set())
    setLastSelectedPlaygroundIndex(null)
    setLastSelectedEditorIndex(null)
  }

  useEffect(() => {
    fetch('http://127.0.0.1:8000/units')
      .then(res => res.json())
      .then(data => {
        setUnits(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Fehler beim Laden der Units:', err)
        setLoading(false)
      })
  }, [])

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div style={{
        padding: '0.5rem 1rem',
        backgroundColor: '#111',
        borderBottom: '1px solid #333',
        display: 'flex',
        gap: '0.7rem'
      }}>
        <button onClick={saveStructureToLocal} style={buttonStyle}>💾 Speichern</button>
        <button onClick={loadStructureFromLocal} style={buttonStyle}>📂 Laden</button>
        <button onClick={resetEditorView} style={buttonStyle}>🔄 Zurücksetzen (UI)</button>
        <button onClick={deleteSavedStructure} style={buttonStyle}>🗑 Speicher löschen</button>
      </div>

      <div style={{
        display: 'flex',
        height: '100vh',
        width: '100vw',
        backgroundColor: '#1a1a1a',
        color: '#eee',
      }}>
        <div style={{ width: '25%', borderRight: '1px solid #333', padding: '1rem', overflowY: 'auto' }}>
          <TreeSidebar units={units} playground={playground} setPlayground={setPlayground} />
        </div>
        <div style={{ width: '40%', padding: '1.5rem', overflowY: 'auto' }}>
          <h2 style={{ marginBottom: '1rem' }}>Ausgewählte Einheiten (Tree)</h2>
          {loading ? (
            <p>⏳ Lade Inhalte …</p>
          ) : (
            <TreePlaygroundView
              playground={playground}
              units={units}
              selectedIDs={selectedPlaygroundIDs}
              setSelectedIDs={setSelectedPlaygroundIDs}
              lastSelectedIndex={lastSelectedPlaygroundIndex}
              setLastSelectedIndex={setLastSelectedPlaygroundIndex}
              setPlayground={setPlayground}
            />
          )}
        </div>
        <div style={{ width: '35%', padding: '1.5rem', borderLeft: '1px solid #333', overflowY: 'auto' }}>
          <h2 style={{ marginBottom: '1rem' }}>📦 Struktur (Tree)</h2>
          <TreeEditorView
            structure={structure}
            setStructure={setStructure}
            selectedEditorIDs={selectedEditorIDs}
            setSelectedEditorIDs={setSelectedEditorIDs}
            lastSelectedEditorIndex={lastSelectedEditorIndex}
            setLastSelectedEditorIndex={setLastSelectedEditorIndex}
            units={units}
          />
        </div>
      </div>
    </DndContext>
  )
}

const buttonStyle = {
  backgroundColor: '#333',
  color: '#eee',
  padding: '0.3rem 0.7rem',
  borderRadius: '4px',
  border: '1px solid #555',
  fontSize: '0.75rem',
  cursor: 'pointer'
}

export default App
