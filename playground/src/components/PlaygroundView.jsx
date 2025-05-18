// src/components/PlaygroundView.jsx
import { useDraggable } from '@dnd-kit/core'

export default function PlaygroundView({
  playground,
  setPlayground,
  selectedIDs,
  setSelectedIDs,
  lastSelectedIndex,
  setLastSelectedIndex,
}) {
  const toggleSelection = (uid, index, shift = false) => {
    setSelectedIDs(prev => {
      const next = new Set(prev)

      if (shift && lastSelectedIndex !== null) {
        const start = Math.min(lastSelectedIndex, index)
        const end = Math.max(lastSelectedIndex, index)
        for (let i = start; i <= end; i++) {
          next.add(playground[i].UnitID)
        }
      } else {
        if (next.has(uid)) {
          next.delete(uid)
        } else {
          next.add(uid)
        }
        setLastSelectedIndex(index)
      }

      return next
    })
  }

  const removeUnit = (uid) => {
    setPlayground(prev => prev.filter(u => u.UnitID !== uid))
    setSelectedIDs(prev => {
      const next = new Set(prev)
      next.delete(uid)
      return next
    })
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
      gap: '0.75rem',
    }}>
      {playground.map((unit, index) => (
        <DraggableUnit
          key={unit.UnitID}
          unit={unit}
          index={index}
          isSelected={selectedIDs.has(unit.UnitID)}
          selectedIDs={selectedIDs}
          onRemove={removeUnit}
          onToggle={toggleSelection}
        />
      ))}
    </div>
  )
}

function DraggableUnit({ unit, index, isSelected, selectedIDs, onRemove, onToggle }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `__drop__${unit.UnitID}`,
    data: {
      type: 'unit',
      draggedIDs: isSelected && selectedIDs.size > 1
        ? Array.from(selectedIDs)
        : [unit.UnitID]
    }
  })

  const style = {
    padding: '0.75rem',
    borderRadius: '8px',
    backgroundColor: isSelected ? '#333' : isDragging ? '#2a2a2a' : '#1e1e1e',
    border: isSelected ? '2px solid #4fc3f7' : '1px solid #444',
    color: '#eee',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
    cursor: 'grab',
    boxShadow: isSelected ? '0 0 0 2px #4fc3f7 inset' : 'none',
    transition: 'all 0.15s ease',
    minHeight: '100px',
    justifyContent: 'space-between'
  }

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={style}
      onClick={(e) => {
        e.stopPropagation()
        onToggle(unit.UnitID, index, e.shiftKey)
      }}
    >
      <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{unit.UnitID}</div>
      <div style={{ fontSize: '0.75rem', color: '#aaa' }}>
        {unit.Name ?? '⟨Kein Name⟩'}
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation()
          onRemove(unit.UnitID)
        }}
        style={{
          alignSelf: 'flex-end',
          marginTop: '0.5rem',
          background: 'transparent',
          border: 'none',
          color: '#aaa',
          fontSize: '1rem',
          cursor: 'pointer',
        }}
        title="Entfernen"
      >
        ✕
      </button>
    </div>
  )
}
