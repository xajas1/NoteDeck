import { useDraggable } from '@dnd-kit/core'

export default function PlaygroundView({ playground, setPlayground }) {
  const removeUnit = (uid) =>
    setPlayground(prev => prev.filter(u => u.UnitID !== uid))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {playground.map(unit => (
        <DraggableUnit key={unit.UnitID} unit={unit} onRemove={removeUnit} />
      ))}
    </div>
  )
}

function DraggableUnit({ unit, onRemove }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `__drop__${unit.UnitID}`,
    data: {
      type: 'unit',
      unitID: unit.UnitID,
      fromSubID: null
    }
  })
  

  const style = {
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    backgroundColor: isDragging ? '#333' : '#2a2a2a',
    color: '#eee',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    opacity: isDragging ? 0.5 : 1,
    cursor: 'grab',
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <span>{unit.UnitID}</span>
      <button
        onClick={() => onRemove(unit.UnitID)}
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
