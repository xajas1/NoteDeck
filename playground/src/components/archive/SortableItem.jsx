import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

export default function SortableItem({ id, index, entry, onUpdate }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    cursor: 'grab'
  }

  return (
    <tr ref={setNodeRef} style={style}>
      <td {...attributes} {...listeners} style={{ textAlign: 'center' }}>{index + 1}</td>
      <td>{entry.UnitID}</td>
      <td>
        <input
          type="text"
          value={entry.Section}
          onChange={(e) => onUpdate('Section', e.target.value)}
          placeholder="z.B. Einführung"
          style={{ width: '100%' }}
        />
      </td>
      <td>
        <input
          type="text"
          value={entry.Subsection}
          onChange={(e) => onUpdate('Subsection', e.target.value)}
          placeholder="z.B. Definition"
          style={{ width: '100%' }}
        />
      </td>
    </tr>
  )
}
