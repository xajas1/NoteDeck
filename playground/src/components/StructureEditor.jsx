// src/components/StructureEditor.jsx
import { useState } from 'react'
import { useDroppable, useDraggable } from '@dnd-kit/core'

export default function StructureEditor({ structure, setStructure }) {
  const addSection = () => {
    const name = prompt("Section-Name eingeben:")
    if (!name?.trim()) return
    const newSection = {
      id: `sec-${Date.now()}`,
      name: name.trim(),
      subsections: []
    }
    setStructure(prev => [...prev, newSection])
  }

  const addSubsection = (sectionID) => {
    const name = prompt("Subsection-Name eingeben:")
    if (!name?.trim()) return
    setStructure(prev =>
      prev.map(sec =>
        sec.id === sectionID
          ? {
              ...sec,
              subsections: [
                ...sec.subsections,
                { id: `sub-${Date.now()}`, name: name.trim(), unitIDs: [] }
              ]
            }
          : sec
      )
    )
  }

  const handleDragEnd = ({ active, over }) => {
    if (!active || !over) return
  
    const draggedID = active.id
    const fromSubID = active.data?.current?.fromSubID
    const toSubID = over.id
  
    if (!fromSubID || !toSubID) return
    if (fromSubID === toSubID) {
      // ✅ Reordering innerhalb derselben Subsection
      setStructure(prev =>
        prev.map(section => ({
          ...section,
          subsections: section.subsections.map(sub => {
            if (sub.id !== fromSubID) return sub
  
            const oldIndex = sub.unitIDs.indexOf(draggedID)
            const newIndex = sub.unitIDs.indexOf(over.data?.current?.unitID)
  
            if (oldIndex < 0 || newIndex < 0 || oldIndex === newIndex) return sub
  
            const reordered = [...sub.unitIDs]
            reordered.splice(oldIndex, 1)
            reordered.splice(newIndex, 0, draggedID)
  
            return { ...sub, unitIDs: reordered }
          })
        }))
      )
    } else {
      // ✅ Verschieben zwischen Subsections
      setStructure(prev =>
        prev.map(section => ({
          ...section,
          subsections: section.subsections.map(sub => {
            if (sub.id === fromSubID) {
              return {
                ...sub,
                unitIDs: sub.unitIDs.filter(id => id !== draggedID)
              }
            }
            if (sub.id === toSubID && !sub.unitIDs.includes(draggedID)) {
              return {
                ...sub,
                unitIDs: [...sub.unitIDs, draggedID]
              }
            }
            return sub
          })
        }))
      )
    }
  }
  

  const handleRemoveUnit = (subID, uid) => {
    setStructure(prev =>
      prev.map(section => ({
        ...section,
        subsections: section.subsections.map(sub =>
          sub.id === subID
            ? { ...sub, unitIDs: sub.unitIDs.filter(id => id !== uid) }
            : sub
        )
      }))
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <button onClick={addSection}>➕ Neue Section</button>

      {structure.map(section => (
        <div
          key={section.id}
          style={{
            border: '1px solid #555',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: '#1e1e1e'
          }}
        >
          <strong>{section.name}</strong>
          <button
            style={{ marginLeft: '0.5rem', fontSize: '0.8rem' }}
            onClick={() => addSubsection(section.id)}
          >
            ➕ Subsection
          </button>

          {section.subsections.length === 0 ? (
            <p style={{ color: '#777' }}>Keine Subsections</p>
          ) : (
            section.subsections.map(sub => (
              <DroppableSubsection
                key={sub.id}
                subsection={sub}
                onRemoveUnit={(uid) => handleRemoveUnit(sub.id, uid)}
              />
            ))
          )}
        </div>
      ))}
    </div>
  )
}

// 🔻 Subsection mit Dropzone
function DroppableSubsection({ subsection, onRemoveUnit }) {
  const { setNodeRef, isOver } = useDroppable({
    id: subsection.id,
    data: { type: 'subsection', id: subsection.id }
  })

  const style = {
    marginTop: '0.5rem',
    padding: '0.5rem',
    border: isOver ? '2px dashed #4fc3f7' : '1px dashed #777',
    borderRadius: '4px',
    backgroundColor: '#2a2a2a',
    transition: '0.2s ease all'
  }

  return (
    <div ref={setNodeRef} style={style}>
      <strong>{subsection.name}</strong>
      <ul style={{ fontSize: '0.9rem', marginTop: '0.5rem', listStyle: 'none', paddingLeft: 0 }}>
        {subsection.unitIDs.length === 0 ? (
          <li style={{ color: '#888' }}>⏳ keine Units</li>
        ) : (
          subsection.unitIDs.map(uid => (
            <DraggableUnit
              key={uid}
              uid={uid}
              fromSubID={subsection.id}
              onRemove={() => onRemoveUnit(uid)}
            />
          ))
        )}
      </ul>
    </div>
  )
}

// 🔻 Drag-fähige einzelne Unit
function DraggableUnit({ uid, fromSubID, onRemove }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: uid,
    data: { type: 'unit', unitID: uid, fromSubID }
  })  
  return (
    <li
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        opacity: isDragging ? 0.5 : 1,
        padding: '0.2rem 0',
        cursor: 'grab',
      }}
    >
      <span>{uid}</span>
      <button
        onClick={onRemove}
        style={{
          marginLeft: '1rem',
          background: 'transparent',
          border: 'none',
          color: '#aaa',
          cursor: 'pointer',
        }}
      >
        ✕
      </button>
    </li>
  )
}
