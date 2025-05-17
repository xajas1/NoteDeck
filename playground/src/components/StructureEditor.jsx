// src/components/StructureEditor.jsx
import { useDroppable } from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

export default function StructureEditor({ structure, setStructure }) {
  const addSection = () => {
    const name = prompt('Section-Name:')
    if (!name?.trim()) return
    setStructure(prev => [...prev, {
      id: `sec-${Date.now()}`,
      name: name.trim(),
      subsections: []
    }])
  }

  const addSubsection = (secID) => {
    const name = prompt('Subsection-Name:')
    if (!name?.trim()) return
    setStructure(prev =>
      prev.map(sec =>
        sec.id === secID
          ? { ...sec, subsections: [...sec.subsections, {
              id: `sub-${Date.now()}`,
              name: name.trim(),
              unitIDs: []
            }] }
          : sec
      )
    )
  }

  const removeUnit = (subID, uid) => {
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
        <div key={section.id} style={styles.section}>
          <strong>{section.name}</strong>
          <button onClick={() => addSubsection(section.id)}>➕ Subsection</button>
          {section.subsections.map(sub => (
            <DroppableSubsection
              key={sub.id}
              subsection={sub}
              onRemoveUnit={removeUnit}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

function DroppableSubsection({ subsection, onRemoveUnit }) {
  const { setNodeRef, isOver } = useDroppable({
    id: subsection.id,
    data: { subsectionId: subsection.id }
  })

  return (
    <div ref={setNodeRef} style={{
      ...styles.subsection,
      borderColor: isOver ? '#4fc3f7' : '#777'
    }}>
      <strong>{subsection.name}</strong>
      <SortableContext
        items={subsection.unitIDs.map(id => `${subsection.id}__${id}`)}
        strategy={verticalListSortingStrategy}
      >
        <ul style={styles.ul}>
          {subsection.unitIDs.map(uid => (
            <SortableUnit
              key={uid}
              id={`${subsection.id}__${uid}`}
              uid={uid}
              fromSubID={subsection.id}
              onRemove={() => onRemoveUnit(subsection.id, uid)}
            />
          ))}
        </ul>
      </SortableContext>
    </div>
  )
}

function SortableUnit({ id, uid, onRemove }) {
  const {
    setNodeRef,
    attributes,
    listeners,
    transform,
    transition,
    isDragging
  } = useSortable({ id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    display: 'flex',
    justifyContent: 'space-between',
    cursor: 'grab',
    padding: '0.2rem 0'
  }

  return (
    <li ref={setNodeRef} {...attributes} {...listeners} style={style}>
      <span>{uid}</span>
      <button onClick={onRemove} style={styles.remove}>✕</button>
    </li>
  )
}

const styles = {
  section: {
    border: '1px solid #555',
    borderRadius: '8px',
    padding: '1rem',
    backgroundColor: '#1e1e1e'
  },
  subsection: {
    marginTop: '0.5rem',
    padding: '0.5rem',
    border: '1px dashed #777',
    borderRadius: '4px',
    backgroundColor: '#2a2a2a',
    transition: '0.2s ease all'
  },
  ul: {
    listStyle: 'none',
    paddingLeft: 0,
    marginTop: '0.5rem',
    fontSize: '0.9rem'
  },
  remove: {
    marginLeft: '1rem',
    background: 'transparent',
    border: 'none',
    color: '#aaa',
    cursor: 'pointer'
  }
}
