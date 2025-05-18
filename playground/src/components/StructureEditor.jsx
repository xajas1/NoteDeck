import { useDroppable } from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

export default function StructureEditor({
  structure,
  setStructure,
  selectedEditorIDs,
  setSelectedEditorIDs,
  lastSelectedEditorIndex,
  setLastSelectedEditorIndex,
  units
}) {
  const toggleEditorSelection = (fullID, index, shift = false, allIDs = []) => {
    setSelectedEditorIDs(prev => {
      const next = new Set(prev)
      if (shift && lastSelectedEditorIndex !== null) {
        const start = Math.min(lastSelectedEditorIndex, index)
        const end = Math.max(lastSelectedEditorIndex, index)
        for (let i = start; i <= end; i++) {
          next.add(allIDs[i])
        }
      } else {
        if (next.has(fullID)) {
          next.delete(fullID)
        } else {
          next.add(fullID)
        }
        setLastSelectedEditorIndex(index)
      }
      return next
    })
  }

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
          ? {
              ...sec,
              subsections: [
                ...sec.subsections,
                {
                  id: `sub-${Date.now()}`,
                  name: name.trim(),
                  unitIDs: []
                }
              ]
            }
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
    setSelectedEditorIDs(prev => {
      const next = new Set(prev)
      next.delete(`${subID}__${uid}`)
      return next
    })
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
              selectedEditorIDs={selectedEditorIDs}
              onRemoveUnit={removeUnit}
              onToggleSelection={toggleEditorSelection}
              lastSelectedEditorIndex={lastSelectedEditorIndex}
              setLastSelectedEditorIndex={setLastSelectedEditorIndex}
              units={units} // ✅ wird weitergegeben
            />
          ))}
        </div>
      ))}
    </div>
  )
}

function DroppableSubsection({
  subsection,
  onRemoveUnit,
  onToggleSelection,
  selectedEditorIDs,
  lastSelectedEditorIndex,
  setLastSelectedEditorIndex,
  units
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
      <strong>{subsection.name}</strong>
      <SortableContext items={allIDs} strategy={verticalListSortingStrategy}>
        <ul style={styles.ul}>
          {subsection.unitIDs.map((uid, index) => {
            const fullID = `${subsection.id}__${uid}`
            const unit = units?.find(u => u.UnitID === uid)
            const name = unit?.Content || '⟨Kein Name⟩'

            return (
              <SortableUnit
                key={fullID}
                id={fullID}
                uid={uid}
                index={index}
                fullID={fullID}
                allIDs={allIDs}
                isSelected={selectedEditorIDs.has(fullID)}
                selectedEditorIDs={selectedEditorIDs}
                onToggleSelection={(shiftKey) =>
                  onToggleSelection(fullID, index, shiftKey, allIDs)
                }
                onRemove={() => onRemoveUnit(subsection.id, uid)}
                name={name}
              />
            )
          })}
        </ul>
      </SortableContext>
    </div>
  )
}

function SortableUnit({
  id,
  uid,
  index,
  fullID,
  isSelected,
  selectedEditorIDs,
  onToggleSelection,
  onRemove,
  allIDs,
  name
}) {
  const {
    setNodeRef,
    attributes,
    listeners,
    transform,
    transition,
    isDragging
  } = useSortable({
    id,
    data: {
      type: 'unit',
      draggedIDs: isSelected && selectedEditorIDs.size > 1
        ? Array.from(selectedEditorIDs).map(x => x.split('__')[1])
        : [uid]
    }
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    display: 'flex',
    justifyContent: 'space-between',
    cursor: 'grab',
    padding: '0.2rem 0',
    border: isSelected ? '1px solid #4fc3f7' : '1px solid transparent',
    backgroundColor: isSelected ? '#333' : 'transparent'
  }

  return (
    <li
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      onClick={(e) => {
        e.stopPropagation()
        onToggleSelection(e.shiftKey)
      }}
      style={style}
    >
      <div>
        <strong>{uid}</strong><br />
        <span style={{ fontSize: '0.75rem', color: '#aaa' }}>{name}</span>
      </div>
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
