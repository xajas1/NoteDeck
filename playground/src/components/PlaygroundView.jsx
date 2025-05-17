// PlaygroundView.jsx
import { useState } from 'react'
import { useDraggable } from '@dnd-kit/core'

export default function PlaygroundView({ playground, setPlayground }) {
  const [selectedIDs, setSelectedIDs] = useState(new Set())
  const [lastSelectedIndex, setLastSelectedIndex] = useState(null)

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
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
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    backgroundColor: isSelected ? '#444' : (isDragging ? '#333' : '#2a2a2a'),
    border: isSelected ? '1px solid #4fc3f7' : '1px solid transparent',
    color: '#eee',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    opacity: isDragging ? 0.5 : 1,
    cursor: 'grab',
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
      <span>{unit.UnitID}</span>
      <button
        onClick={(e) => {
          e.stopPropagation()
          onRemove(unit.UnitID)
        }}
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
    </div>
  )
}
