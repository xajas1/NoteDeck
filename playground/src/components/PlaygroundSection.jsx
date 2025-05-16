import { useDroppable } from '@dnd-kit/core'
import { useState, useEffect } from 'react'

export default function PlaygroundSection({ sectionID, title, children, onRename }) {
  const { setNodeRef, isOver } = useDroppable({
    id: sectionID,
    data: { type: 'section', sectionID }
  })

  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(title)

  // Synchronisiere `value` mit aktualisiertem `title`
  useEffect(() => {
    if (!editing) setValue(title)
  }, [title, editing])

  const handleBlur = () => {
    setEditing(false)
    const trimmed = value.trim()
    if (trimmed && trimmed !== title && typeof onRename === 'function') {
      onRename(trimmed)
    } else {
      setValue(title)
    }
  }

  const style = {
    border: `2px dashed ${isOver ? '#4fc3f7' : '#555'}`,
    padding: '1rem',
    borderRadius: '10px',
    backgroundColor: '#1e1e1e',
    transition: '0.2s ease all',
    minHeight: '4rem'
  }

  return (
    <div ref={setNodeRef} style={style}>
      <div style={{ marginBottom: '0.5rem', color: '#eee' }}>
        {editing ? (
          <input
            autoFocus
            value={value}
            onChange={e => setValue(e.target.value)}
            onBlur={handleBlur}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                e.preventDefault()
                handleBlur()
              } else if (e.key === 'Escape') {
                setEditing(false)
                setValue(title)
              }
            }}
            style={{
              fontSize: '1rem',
              backgroundColor: '#333',
              color: '#eee',
              border: '1px solid #777',
              padding: '0.2rem 0.5rem',
              borderRadius: '5px',
              width: '100%'
            }}
          />
        ) : (
          <h3
            onClick={() => setEditing(true)}
            style={{ cursor: 'pointer', margin: 0 }}
          >
            {title || <em>⟨ohne Titel⟩</em>}
          </h3>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {children}
      </div>
    </div>
  )
}
