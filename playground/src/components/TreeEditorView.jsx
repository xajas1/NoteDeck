// src/components/TreeEditorView.jsx
import { useDroppable } from '@dnd-kit/core'

export default function TreeEditorView({ structure, units, selectedEditorIDs, setSelectedEditorIDs, lastSelectedEditorIndex, setLastSelectedEditorIndex }) {
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

  return (
    <div style={{ fontFamily: 'monospace', fontSize: '0.9rem', color: '#eee' }}>
      {structure.map(section => (
        <div key={section.id}>
          <div style={styles.section}>📁 {section.name}</div>
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

function DroppableSubsection({ subsection, getNameByID, selectedEditorIDs, toggleSelection, lastSelectedEditorIndex, setLastSelectedEditorIndex }) {
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
      <div style={styles.subsectionName}>📄 {subsection.name}</div>
      <ul style={styles.ul}>
        {subsection.unitIDs.map((uid, index) => {
          const fullID = `${subsection.id}__${uid}`
          const name = getNameByID(uid)
          return (
            <li
              key={fullID}
              onClick={(e) => toggleSelection(fullID, index, e.shiftKey, allIDs)}
              style={{
                padding: '0.15rem 0.3rem',
                cursor: 'pointer',
                backgroundColor: selectedEditorIDs.has(fullID) ? '#2a2a2a' : 'transparent',
                borderLeft: selectedEditorIDs.has(fullID) ? '3px solid #4fc3f7' : '3px solid transparent'
              }}
            >
              🔹 <strong>{uid}</strong>: <span style={{ color: '#aaa' }}>{name}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

const styles = {
  section: {
    fontWeight: 'bold',
    marginTop: '1rem',
  },
  subsection: {
    marginLeft: '1rem',
    padding: '0.3rem 0.5rem',
    border: '1px dashed #777',
    borderRadius: '4px',
    backgroundColor: '#1e1e1e',
    marginTop: '0.5rem',
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
