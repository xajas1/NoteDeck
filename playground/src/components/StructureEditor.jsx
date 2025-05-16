import {
  DndContext,
  useDroppable,
  useSensor,
  useSensors,
  PointerSensor
} from '@dnd-kit/core'
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

export default function StructureEditor({ structure, setStructure }) {
  const sensors = useSensors(useSensor(PointerSensor))

  const handleDragEnd = ({ active, over }) => {
    if (!active || !over) return

    const activeId = active.id
    const overId = over.id
    const overSubID = over.data?.current?.subsectionId || overId

    // 🟢 Externe Unit aus Playground
    if (activeId.startsWith('__drop__')) {
      const unitID = activeId.replace('__drop__', '')
      const subID = overId.replace('__drop__', '')
      setStructure(prev =>
        prev.map(section => ({
          ...section,
          subsections: section.subsections.map(sub =>
            sub.id === subID && !sub.unitIDs.includes(unitID)
              ? { ...sub, unitIDs: [...sub.unitIDs, unitID] }
              : sub
          )
        }))
      )
      return
    }

    // 🔁 Interner Move
    const [fromSubID, unitID] = activeId.split('__')
    const [toSubID, overUnitID] = overId.split('__')

    if (fromSubID === toSubID) {
      setStructure(prev =>
        prev.map(section => ({
          ...section,
          subsections: section.subsections.map(sub => {
            if (sub.id !== fromSubID) return sub
            const oldIndex = sub.unitIDs.indexOf(unitID)
            const newIndex = sub.unitIDs.indexOf(overUnitID)
            if (oldIndex < 0 || newIndex < 0 || oldIndex === newIndex) return sub
            const reordered = [...sub.unitIDs]
            reordered.splice(oldIndex, 1)
            reordered.splice(newIndex, 0, unitID)
            return { ...sub, unitIDs: reordered }
          })
        }))
      )
    } else {
      setStructure(prev =>
        prev.map(section => ({
          ...section,
          subsections: section.subsections.map(sub => {
            if (sub.id === fromSubID) {
              return {
                ...sub,
                unitIDs: sub.unitIDs.filter(id => id !== unitID)
              }
            }
            if (sub.id === toSubID && !sub.unitIDs.includes(unitID)) {
              return {
                ...sub,
                unitIDs: [...sub.unitIDs, unitID]
              }
            }
            return sub
          })
        }))
      )
    }
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {structure.map(section => (
          <div key={section.id} style={styles.section}>
            <strong>{section.name}</strong>
            {section.subsections.map(sub => (
              <DroppableSubsection key={sub.id} subsection={sub} />
            ))}
          </div>
        ))}
      </div>
    </DndContext>
  )
}

function DroppableSubsection({ subsection }) {
  const { setNodeRef, isOver } = useDroppable({
    id: `__drop__${subsection.id}`,
    data: { subsectionId: subsection.id }
  })

  const items = [
    ...subsection.unitIDs.map(uid => `${subsection.id}__${uid}`),
    `__drop__${subsection.id}`
  ]

  return (
    <div ref={setNodeRef} style={{
      ...styles.subsection,
      borderColor: isOver ? '#4fc3f7' : '#777'
    }}>
      <strong>{subsection.name}</strong>
      <SortableContext items={items} strategy={verticalListSortingStrategy}>
        <ul style={styles.ul}>
          {subsection.unitIDs.map(uid => (
            <SortableUnit
              key={uid}
              id={`${subsection.id}__${uid}`}
              uid={uid}
            />
          ))}

          {/* 👇 Unsichtbarer Drop-Target für externe Einheiten */}
          <li
            key={`__drop__${subsection.id}`}
            id={`__drop__${subsection.id}`}
            style={{ height: '0.5rem' }}
          />
        </ul>
      </SortableContext>
    </div>
  )
}

function SortableUnit({ id, uid }) {
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
  }
}
