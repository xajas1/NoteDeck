// playground/src/App.jsx
import React, { useEffect, useState } from 'react'
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

  const [projects, setProjects] = useState({})
  const [activeProject, setActiveProject] = useState("")
  const [structure, setStructure] = useState([])
  const [playground, setPlayground] = useState([])

  const [selectedIDs, setSelectedIDs] = useState(new Set())
  const [lastSelectedIndex, setLastSelectedIndex] = useState(null)

  const [selectedEditorIDs, setSelectedEditorIDs] = useState(new Set())
  const [lastSelectedEditorIndex, setLastSelectedEditorIndex] = useState(null)

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))
  const STORAGE_KEY = "notedeck_projects_v1"

  const isModified = () => {
    const saved = projects[activeProject]
    if (!saved) return false
    return (
      JSON.stringify(saved.structure) !== JSON.stringify(structure) ||
      JSON.stringify(saved.playground) !== JSON.stringify(playground)
    )
  }

  const saveProjectsToStorage = (updatedProjects, selectedProject) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      projects: updatedProjects,
      activeProject: selectedProject
    }))
  }

  const saveCurrentProject = () => {
    if (!activeProject) return alert("⚠️ Kein aktives Projekt ausgewählt.")
    const updated = {
      ...projects,
      [activeProject]: {
        structure,
        playground,
        timestamp: Date.now()
      }
    }
    setProjects(updated)
    saveProjectsToStorage(updated, activeProject)
    alert(`✅ Projekt '${activeProject}' gespeichert.`)
  }

  const loadProject = (name) => {
    const entry = projects[name]
    if (!entry) return
    setStructure(entry.structure || [])
    setPlayground(entry.playground || [])
    setActiveProject(name)
    saveProjectsToStorage(projects, name)
    setSelectedIDs(new Set())
    setLastSelectedIndex(null)
    setSelectedEditorIDs(new Set())
    setLastSelectedEditorIndex(null)
  }

  const deleteProject = (name) => {
    if (!window.confirm(`❌ Projekt '${name}' wirklich löschen?`)) return
    const copy = { ...projects }
    delete copy[name]
    const nextActive = Object.keys(copy)[0] || ""
    setProjects(copy)
    setActiveProject(nextActive)
    setStructure(copy[nextActive]?.structure || [])
    setPlayground(copy[nextActive]?.playground || [])
    saveProjectsToStorage(copy, nextActive)
    setSelectedIDs(new Set())
    setLastSelectedIndex(null)
    setSelectedEditorIDs(new Set())
    setLastSelectedEditorIndex(null)
  }

  const createNewProject = () => {
    const name = prompt("🔧 Neuer Projektname:")
    if (!name || name.trim() === "") return
    if (projects[name]) return alert("❗ Projektname existiert bereits.")
    const updated = {
      ...projects,
      [name]: { structure: [], playground: [], timestamp: Date.now() }
    }
    setProjects(updated)
    setActiveProject(name)
    setStructure([])
    setPlayground([])
    saveProjectsToStorage(updated, name)
    setSelectedIDs(new Set())
    setLastSelectedIndex(null)
    setSelectedEditorIDs(new Set())
    setLastSelectedEditorIndex(null)
  }

  const renameProject = () => {
    if (!activeProject || !projects[activeProject]) return
    const newName = prompt("📝 Neuer Projektname:", activeProject)
    if (!newName || newName.trim() === "") return
    if (projects[newName] && newName !== activeProject) {
      alert("❗ Ein Projekt mit diesem Namen existiert bereits.")
      return
    }

    const updated = { ...projects }
    updated[newName] = updated[activeProject]
    if (newName !== activeProject) delete updated[activeProject]

    setProjects(updated)
    setActiveProject(newName)
    saveProjectsToStorage(updated, newName)
  }

  const resetToSavedProjectState = () => {
    if (!activeProject || !projects[activeProject]) {
      alert("⚠️ Kein gespeicherter Stand verfügbar.")
      return
    }

    const saved = projects[activeProject]
    setStructure(saved.structure || [])
    setPlayground(saved.playground || [])
    setSelectedIDs(new Set())
    setLastSelectedIndex(null)
    setSelectedEditorIDs(new Set())
    setLastSelectedEditorIndex(null)
    alert("↩ Projekt auf gespeicherten Zustand zurückgesetzt.")
  }

  const handleDragEnd = ({ active, over }) => {
    if (!active || !over || active.id === over.id) return

    const draggedIDs = active?.data?.current?.draggedIDs || [active.id.split('__').pop()]
    const targetSubID = over.id.includes('__') ? over.id.split('__')[0] : over.id
    const targetIndexUnit = over.id.includes('__') ? over.id.split('__')[1] : null

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

    // Auswahl zurücksetzen nach Drag & Drop
    setSelectedIDs(new Set())
    setLastSelectedIndex(null)
    setSelectedEditorIDs(new Set())
    setLastSelectedEditorIndex(null)
  }


  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setSelectedIDs(new Set())
        setLastSelectedIndex(null)
        setSelectedEditorIDs(new Set())
        setLastSelectedEditorIndex(null)
      }
    }
  
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])
  
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

    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      setProjects(parsed.projects || {})
      setActiveProject(parsed.activeProject || "")
      if (parsed.activeProject && parsed.projects?.[parsed.activeProject]) {
        setStructure(parsed.projects[parsed.activeProject].structure || [])
        setPlayground(parsed.projects[parsed.activeProject].playground || [])
      }
    }
  }, [])

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div style={{
        height: '100vh',
        width: '100vw',
        backgroundColor: '#1a1a1a',
        color: '#eee',
        display: 'flex',
        flexDirection: 'column'
      }}>
        
        {/* Topbar */}
        <div style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.7rem', borderBottom: '1px solid #444', backgroundColor: '#111' }}>
          <span>Projekt:</span>
          <select
            value={activeProject}
            onChange={e => loadProject(e.target.value)}
            style={{ padding: '0.2rem 0.4rem', backgroundColor: '#222', color: '#eee', border: '1px solid #555' }}
          >
            {Object.keys(projects).map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
          <button onClick={renameProject} style={topbarButton}>📝 Umbenennen</button>
          <button onClick={createNewProject} style={topbarButton}>➕ Neu</button>
          <button onClick={saveCurrentProject} style={topbarButton}>💾 Speichern</button>
          <button onClick={() => loadProject(activeProject)} style={topbarButton}>📂 Laden</button>
          <button onClick={resetToSavedProjectState} style={topbarButton}>↩ Wiederherstellen</button>
          <button onClick={() => deleteProject(activeProject)} style={topbarButton}>🗑️ Löschen</button>
        </div>

        {/* Main content area */}
        <div style={{ display: 'flex', flexGrow: 1, height: 0 }}>
          <div style={{
            width: '20%',
            borderRight: '1px solid #333',
            padding: '1rem',
            overflowY: 'auto',
            height: '100%'
          }}>
            <TreeSidebar units={units} playground={playground} setPlayground={setPlayground} />
          </div>
          <div style={{
            width: '35%',
            padding: '1.5rem',
            overflowY: 'auto',
            height: '100%'
          }}>
            <h2 style={{ marginBottom: '1rem' }}>Ausgewählte Einheiten (Tree)</h2>
            {loading ? (
              <p>⏳ Lade Inhalte …</p>
            ) : (
              <TreePlaygroundView
                playground={playground}
                units={units}
                selectedIDs={selectedIDs}
                setSelectedIDs={setSelectedIDs}
                lastSelectedIndex={lastSelectedIndex}
                setLastSelectedIndex={setLastSelectedIndex}
                setPlayground={setPlayground}
              />
            )}
          </div>
          <div style={{
            width: '45%',
            padding: '1.5rem',
            borderLeft: '1px solid #333',
            overflowY: 'auto',
            height: '100%'
          }}>
            <h2 style={{ marginBottom: '1rem' }}>📦 Struktur (Tree)</h2>
            <TreeEditorView
              structure={structure}
              setStructure={setStructure}
              selectedEditorIDs={selectedEditorIDs}
              setSelectedEditorIDs={setSelectedEditorIDs}
              lastSelectedEditorIndex={lastSelectedEditorIndex}
              setLastSelectedEditorIndex={setLastSelectedEditorIndex}
              units={units}
              updateStructure={setStructure}
            />
          </div>
        </div>
      </div>
    </DndContext>
  )
}

const topbarButton = {
  backgroundColor: '#333',
  color: '#eee',
  padding: '0.3rem 0.6rem',
  borderRadius: '4px',
  border: '1px solid #555',
  fontSize: '0.75rem',
  cursor: 'pointer'
}

export default App
