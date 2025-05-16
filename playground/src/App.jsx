// src/App.jsx
import { useEffect, useState } from 'react'
import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'

import Sidebar from './components/Sidebar'
import PlaygroundView from './components/PlaygroundView'
import StructureEditor from './components/StructureEditor'

function App() {
  const [units, setUnits] = useState([])
  const [loading, setLoading] = useState(true)
  const [playground, setPlayground] = useState([])
  const [structure, setStructure] = useState([])

  // 👉 Aktiviere PointerSensor (Maus)
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    })
  )

  // 🟡 Wenn Drag startet
  const handleDragStart = (event) => {
    console.log('🟡 Drag Start:', event.active.id)
  }

  // 🟠 Wenn Maus über ein Ziel schwebt
  const handleDragOver = ({ active, over }) => {
    console.log('🟠 Drag Over:', {
      active: active?.id,
      over: over?.id,
    })
  }

  // ✅ Wenn Drop erfolgt
  const handleDragEnd = ({ active, over }) => {
    if (!active || !over) return

    const draggedID = active.id
    const targetSubID = over.id

    console.log(`✅ Drop: ${draggedID} → ${targetSubID}`)

    setStructure(prev =>
      prev.map(section => ({
        ...section,
        subsections: section.subsections.map(sub =>
          sub.id === targetSubID && !sub.unitIDs.includes(draggedID)
            ? { ...sub, unitIDs: [...sub.unitIDs, draggedID] }
            : sub
        )
      }))
    )
  }

  // Lade Units
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
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div
        style={{
          display: 'flex',
          height: '100vh',
          backgroundColor: '#1a1a1a',
          color: '#eee',
        }}
      >
        {/* 🔹 Linke Spalte */}
        <div
          style={{
            width: '20%',
            borderRight: '1px solid #333',
            padding: '1rem',
            overflowY: 'auto',
          }}
        >
          <Sidebar
            units={units}
            playground={playground}
            setPlayground={setPlayground}
          />
        </div>

        {/* 🔹 Mittlere Spalte */}
        <div
          style={{
            width: '50%',
            padding: '2rem',
            overflowY: 'auto',
          }}
        >
          <h2>📄 Ausgewählte Einheiten</h2>
          {loading ? (
            <p>⏳ Lade Inhalte …</p>
          ) : (
            <PlaygroundView
              playground={playground}
              setPlayground={setPlayground}
            />
          )}
        </div>

        {/* 🔹 Rechte Spalte */}
        <div
          style={{
            width: '30%',
            padding: '1rem',
            borderLeft: '1px solid #333',
            overflowY: 'auto',
          }}
        >
          <h2>📦 Struktur</h2>
          <StructureEditor
            structure={structure}
            setStructure={setStructure}
          />
        </div>
      </div>
    </DndContext>
  )
}

export default App
