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
import ExportButton from './components/ExportButton'

function App() {
  const [units, setUnits] = useState([])
  const [loading, setLoading] = useState(true)

  const [projects, setProjects] = useState({})
  const [activeProject, setActiveProject] = useState("")
  const [structure, setStructure] = useState([])
  const [playground, setPlayground] = useState([])

  const [selectedUIDs, setSelectedUIDs] = useState(new Set())
  const [lastSelectedIndex, setLastSelectedIndex] = useState(null)

  const [selectedEditorUIDs, setSelectedEditorUIDs] = useState(new Set())
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

  const backupAllProjects = () => {
    Object.entries(projects).forEach(([name, data]) => {
      const payload = {
        projectName: name,
        structure: data.structure || [],
        playground: data.playground || []
      }

      fetch(`http://127.0.0.1:8000/export-project/${name}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }).then(res => res.json())
        .then(r => console.log(`✅ Backup: ${name}`, r))
        .catch(err => console.warn(`❌ Fehler bei ${name}`, err))
    })

    alert("📦 Alle Projekte gesichert.")
  }

  const loadProject = (name) => {
    const entry = projects[name]
    if (!entry) return
    setStructure(entry.structure || [])
    setPlayground(entry.playground || [])
    setActiveProject(name)
    saveProjectsToStorage(projects, name)
    setSelectedUIDs(new Set())
    setLastSelectedIndex(null)
    setSelectedEditorUIDs(new Set())
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
    setSelectedUIDs(new Set())
    setLastSelectedIndex(null)
    setSelectedEditorUIDs(new Set())
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
    setSelectedUIDs(new Set())
    setLastSelectedIndex(null)
    setSelectedEditorUIDs(new Set())
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
    setSelectedUIDs(new Set())
    setLastSelectedIndex(null)
    setSelectedEditorUIDs(new Set())
    setLastSelectedEditorIndex(null)
    alert("↩ Projekt auf gespeicherten Zustand zurückgesetzt.")
  }

  const handleDragEnd = ({ active, over }) => {
    if (!active || !over || active.id === over.id) return

    const draggedUIDs = active?.data?.current?.draggedIDs || [active.id.split('__').pop()]
    const targetSubID = over.id.includes('__') ? over.id.split('__')[0] : over.id
    const targetUID = over.id.includes('__') ? over.id.split('__')[1] : null

    setStructure(prev => {
      return prev.map(section => ({
        ...section,
        subsections: section.subsections.map(sub => {
          const isTarget = sub.id === targetSubID
          const original = sub.unitUIDs

          const cleaned = original.filter(uid => !draggedUIDs.includes(uid))

          if (!isTarget) return { ...sub, unitUIDs: cleaned }
 
          let insertAt = cleaned.length
          if (targetUID) {
            const targetIndexOriginal = original.indexOf(targetUID)
            const firstDraggedIndex = Math.min(...draggedUIDs.map(uid => original.indexOf(uid)).filter(i => i !== -1))
            const direction = firstDraggedIndex < targetIndexOriginal ? 'down' : 'up'
            let correctedIndex = cleaned.findIndex(uid => uid === targetUID)
            if (correctedIndex === -1) correctedIndex = cleaned.length
            if (direction === 'down') correctedIndex++
            insertAt = Math.min(correctedIndex, cleaned.length)
          }

          const result = [...cleaned]
          result.splice(insertAt, 0, ...draggedUIDs)
          return { ...sub, unitUIDs: result }
        })
      }))
    })

    const fullUIDs = draggedUIDs.map(uid => `${targetSubID}__${uid}`)
    setSelectedEditorUIDs(new Set(fullUIDs))
    setLastSelectedEditorIndex(null)
    setSelectedUIDs(new Set())
    setLastSelectedIndex(null)
  }

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setSelectedUIDs(new Set())
        setLastSelectedIndex(null)
        setSelectedEditorUIDs(new Set())
        setLastSelectedEditorIndex(null)
      }
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === "s") {
        e.preventDefault()
        backupAllProjects()
      }
    }

    const handleBeforeUnload = () => {
      if (!activeProject || !projects[activeProject]) return
      const body = {
        projectName: activeProject,
        structure,
        playground
      }
      navigator.sendBeacon(
        `http://127.0.0.1:8000/export-project/${activeProject}`,
        new Blob([JSON.stringify(body)], { type: 'application/json' })
      )
    }

    window.addEventListener("keydown", handleKeyDown)
    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => {
      window.removeEventListener("keydown", handleKeyDown)
      window.removeEventListener("beforeunload", handleBeforeUnload)
    }
  }, [activeProject, structure, playground, projects])

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
      <div style={{ height: '100vh', width: '100vw', backgroundColor: '#1a1a1a', color: '#eee', display: 'flex', flexDirection: 'column' }}>
        {/* Topbar */}
        <div style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.7rem', borderBottom: '1px solid #444', backgroundColor: '#111' }}>
          <span>Projekt:</span>
          <select
            value={activeProject}
            onChange={e => loadProject(e.target.value)}
            style={{ padding: '0.2rem 0.4rem', backgroundColor: '#222', color: '#eee', border: '1px solid #555' }}
          >
            {Object.keys(projects).map(name => {
              const isDirty =
                name === activeProject &&
                (JSON.stringify(projects[name]?.structure) !== JSON.stringify(structure) ||
                 JSON.stringify(projects[name]?.playground) !== JSON.stringify(playground))
              return (
                <option key={name} value={name}>{isDirty ? `${name} *` : name}</option>
              )
            })}
          </select>
          <button onClick={renameProject} style={topbarButton}>📝 Umbenennen</button>
          <button onClick={createNewProject} style={topbarButton}>➕ Neu</button>
          <button onClick={saveCurrentProject} style={topbarButton}>💾 Speichern</button>
          <button onClick={() => loadProject(activeProject)} style={topbarButton}>📂 Laden</button>
          <button onClick={resetToSavedProjectState} style={topbarButton}>↩ Wiederherstellen</button>
          <button onClick={() => deleteProject(activeProject)} style={topbarButton}>🗑️ Löschen</button>
          <ExportButton projectName={activeProject} structure={structure} />
          <button onClick={backupAllProjects} style={{ ...topbarButton, backgroundColor: '#446' }}>📦 Backup alle</button>
        </div>

        {/* Main content area */}
        <div style={{ display: 'flex', flexGrow: 1, height: 0 }}>
          <div style={{
            width: '20%',
            borderRight: '1px solid #333',
            padding: '1rem',
            overflowY: 'auto',
            overscrollBehavior: 'contain',
            height: '100%'
          }}>
            <TreeSidebar units={units} playground={playground} setPlayground={setPlayground} />
          </div>
          <div style={{
            width: '35%',
            padding: '1.5rem',
            overflowY: 'auto',
            overscrollBehavior: 'contain',
            height: '100%'
          }}>
            <h2 style={{ marginBottom: '1rem' }}>Ausgewählte Einheiten (Tree)</h2>
            {loading ? (
              <p>⏳ Lade Inhalte …</p>
            ) : (
              <TreePlaygroundView
                playground={playground}
                units={units}
                selectedUIDs={selectedUIDs}
                setSelectedUIDs={setSelectedUIDs}
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
            overscrollBehavior: 'contain',
            height: '100%'
          }}>
            <h2 style={{ marginBottom: '1rem' }}>📦 Struktur (Tree)</h2>
            <TreeEditorView
              structure={structure}
              setStructure={setStructure}
              selectedEditorUIDs={selectedEditorUIDs}
              setSelectedEditorUIDs={setSelectedEditorUIDs}
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
