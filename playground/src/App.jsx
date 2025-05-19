// src/App.jsx
import { useEffect, useState } from 'react'
import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors
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
      activationConstraint: { distance: 5 }
    })
  )

  const normalizeUnitID = (id) => {
    if (typeof id !== 'string') return id
    if (id.includes('__')) return id.split('__')[1]
    if (id.includes('____drop__')) return id.split('____drop__')[1]
    if (id.includes('__drop__')) return id.split('__drop__')[1]
    return id
  }

  const normalizeSubsectionID = (id) => {
    if (typeof id !== 'string') return id
    return id.includes('__') ? id.split('__')[0] : id
  }

  const handleDragEnd = ({ active, over }) => {
    if (!active || !over || active.id === over.id) return

    const activeType = active.data.current?.type
    const overId = over.id

    // === 1. Section-Verschiebung ===
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
      return
    }

    // === 2. Subsection-Verschiebung ===
    if (activeType === 'subsection') {
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
      return
    }

    // === 3. Unit-Verschiebung ===
    const draggedIDs =
      active?.data?.current?.draggedIDs?.map(normalizeUnitID) ||
      (selectedPlaygroundIDs.size > 0
        ? Array.from(selectedPlaygroundIDs).map(normalizeUnitID)
        : selectedEditorIDs.size > 0
        ? Array.from(selectedEditorIDs).map(normalizeUnitID)
        : [normalizeUnitID(active.id)])

    const targetSubID = normalizeSubsectionID(over.id)
    const targetUID = normalizeUnitID(over.id)

    setStructure(prev =>
      prev.map(section => ({
        ...section,
        subsections: section.subsections.map(sub => {
          const isTarget = sub.id === targetSubID
          const isSource = draggedIDs.some(id => sub.unitIDs.includes(id))

          // Entferne draggedIDs aus allen Subsections
          let filtered = sub.unitIDs.filter(id => !draggedIDs.includes(id))

          if (isTarget) {
            let insertAt = filtered.length

            if (filtered.includes(targetUID)) {
              insertAt = filtered.indexOf(targetUID)

              // Bei Self-Drop innerhalb derselben Subsection
              if (isSource) {
                const fromIndex = sub.unitIDs.indexOf(draggedIDs[0])
                const toIndex = sub.unitIDs.indexOf(targetUID)
                if (fromIndex < toIndex) insertAt += 1
              }
            }

            draggedIDs.forEach((id, i) => {
              if (!filtered.includes(id)) {
                filtered.splice(insertAt + i, 0, id)
              }
            })
          }

          return { ...sub, unitIDs: filtered }
        })
      }))
    )

    // Reset selection
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
      <div
        style={{
          display: 'flex',
          height: '100vh',
          width: '100vw',
          backgroundColor: '#1a1a1a',
          color: '#eee'
        }}
      >
        <div style={{ width: '25%', borderRight: '1px solid #333', padding: '1rem', overflowY: 'auto' }}>
          <TreeSidebar units={units} playground={playground} setPlayground={setPlayground} />
        </div>

        <div style={{ width: '40%', padding: '1.5rem', overflowY: 'auto' }}>
          <h2 style={{ marginBottom: '1rem' }}>Ausgewählte Einheiten</h2>
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
          <h2 style={{ marginBottom: '1rem' }}>📦 Struktur</h2>
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

export default App
