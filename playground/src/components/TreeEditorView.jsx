// src/components/TreeEditorView.jsx
import { useState } from 'react'
import { useDroppable, useDraggable } from '@dnd-kit/core'

export default function TreeEditorView({
  structure,
  setStructure,
  units,
  selectedEditorIDs,
  setSelectedEditorIDs,
  lastSelectedEditorIndex,
  setLastSelectedEditorIndex
}) {
  const [newSectionName, setNewSectionName] = useState('')
  const [subInputs, setSubInputs] = useState({})

  const getNameByID = (id) => units.find(u => u.UnitID === id)?.Content || '⟨Kein Name⟩'

  const toggleSelection = (fullID, index, shift = false, allIDs = []) => {
    setSelectedEditorIDs(prev => {
      const next = new Set(prev)
      if (shift && lastSelectedEditorIndex !== null) {
        const start = Math.min(lastSelectedEditorIndex, index)
        const end = Math.max(lastSelectedEditorIndex, index)
        for (let i = start; i <= end; i++) {
          next.add(allIDs[i])
        }
      } else {
        if (next.has(fullID)) next.delete(fullID)
        else next.add(fullID)
        setLastSelectedEditorIndex(index)
      }
      return next
    })
  }

  const addSection = () => {
    if (!newSectionName.trim()) return
    setStructure([...structure, {
      id: `sec-${Date.now()}`,
      name: newSectionName,
      subsections: []
    }])
    setNewSectionName('')
  }

  const addSubsection = (sectionId, name) => {
    if (!name.trim()) return
    setStructure(prev => prev.map(s =>
      s.id === sectionId
        ? { ...s, subsections: [...s.subsections, { id: `sub-${Date.now()}`, name, unitIDs: [] }] }
        : s
    ))
    setSubInputs({ ...subInputs, [sectionId]: '' })
  }

  return (
    <div style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: '#eee' }}>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <input
          type="text"
          value={newSectionName}
          onChange={e => setNewSectionName(e.target.value)}
          placeholder="Neue Section"
          style={{ backgroundColor: '#111', color: '#eee', padding: '0.4rem', flex: 1 }}
        />
        <button onClick={addSection} style={styles.button}>Add</button>
      </div>

      {structure.map(section => (
        <div key={section.id}>
          <div style={styles.section}>{section.name}</div>

          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', marginLeft: '1rem' }}>
            <input
              type="text"
              value={subInputs[section.id] || ''}
              onChange={e => setSubInputs({ ...subInputs, [section.id]: e.target.value })}
              placeholder="Neue Subsection"
              style={{ backgroundColor: '#111', color: '#eee', padding: '0.3rem', flex: 1 }}
            />
            <button onClick={() => addSubsection(section.id, subInputs[section.id] || '')} style={styles.subButton}>
              Add
            </button>
          </div>

          {section.subsections.map(sub => (
            <DroppableSubsection
              key={sub.id}
              subsection={sub}
              getNameByID={getNameByID}
              selectedEditorIDs={selectedEditorIDs}
              toggleSelection={toggleSelection}
              lastSelectedEditorIndex={lastSelectedEditorIndex}
              setLastSelectedEditorIndex={setLastSelectedEditorIndex}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

function DroppableSubsection({
  subsection,
  getNameByID,
  selectedEditorIDs,
  toggleSelection,
  lastSelectedEditorIndex,
  setLastSelectedEditorIndex
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: subsection.id,
    data: { subsectionId: subsection.id }
  })

  const allIDs = subsection.unitIDs.map(id => `${subsection.id}__${id}`)

  return (
    <div
      ref={setNodeRef}
      style={{
        ...styles.subsection,
        borderColor: isOver ? '#4fc3f7' : '#777'
      }}
    >
      <div style={styles.subsectionName}>{subsection.name}</div>
      <ul style={styles.ul}>
        {subsection.unitIDs.map((uid, index) => {
          const fullID = `${subsection.id}__${uid}`
          const name = getNameByID(uid)
          return (
            <DraggableEditorLine
              key={fullID}
              fullID={fullID}
              uid={uid}
              name={name}
              index={index}
              selectedEditorIDs={selectedEditorIDs}
              toggleSelection={toggleSelection}
              lastSelectedEditorIndex={lastSelectedEditorIndex}
              allIDs={allIDs}
            />
          )
        })}
      </ul>
    </div>
  )
}

function DraggableEditorLine({
  fullID,
  uid,
  name,
  index,
  selectedEditorIDs,
  toggleSelection,
  lastSelectedEditorIndex,
  allIDs
}) {
  const { attributes, listeners, setNodeRef } = useDraggable({
    id: fullID,
    data: {
      type: 'unit',
      draggedIDs: selectedEditorIDs.size > 0 ? Array.from(selectedEditorIDs).map(f => f.split('__')[1]) : [uid]
    }
  })

  return (
    <li
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      onClick={(e) => toggleSelection(fullID, index, e.shiftKey, allIDs)}
      style={{
        padding: '0.15rem 0.3rem',
        cursor: 'pointer',
        backgroundColor: selectedEditorIDs.has(fullID) ? '#2a2a2a' : 'transparent',
        borderLeft: selectedEditorIDs.has(fullID) ? '3px solid #4fc3f7' : '3px solid transparent'
      }}
    >
      <strong>{uid}</strong>: <span style={{ color: '#aaa' }}>{name}</span>
    </li>
  )
}

const styles = {
  button: {
    backgroundColor: '#333',
    color: '#eee',
    padding: '0.4rem 0.8rem',
    borderRadius: '5px',
    border: 'none',
    cursor: 'pointer'
  },
  subButton: {
    backgroundColor: '#222',
    color: '#ccc',
    padding: '0.3rem 0.7rem',
    borderRadius: '4px',
    border: 'none',
    fontSize: '0.78rem',
    cursor: 'pointer'
  },
  section: {
    fontWeight: 'bold',
    marginTop: '1rem',
    fontSize: '0.92rem'
  },
  subsection: {
    marginLeft: '1rem',
    padding: '0.3rem 0.5rem',
    border: '1px dashed #777',
    borderRadius: '4px',
    backgroundColor: '#1e1e1e',
    marginTop: '0.5rem'
  },
  subsectionName: {
    fontStyle: 'italic',
    marginBottom: '0.3rem',
  },
  ul: {
    listStyle: 'none',
    paddingLeft: '1rem',
    margin: 0
  }
}
