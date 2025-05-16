import { DndContext, closestCenter } from '@dnd-kit/core'
import { arrayMove, SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { useMemo } from 'react'
import SortableItem from './SortableItem'

export default function PlaygroundGrouped({ playground, setPlayground }) {
  const sections = useMemo(() => {
    const grouped = {}
    for (const entry of playground) {
      if (!grouped[entry.Section]) grouped[entry.Section] = []
      grouped[entry.Section].push(entry)
    }
    return grouped
  }, [playground])

  const handleDragEnd = (event) => {
    const { active, over } = event
    if (!over || active.id === over.id) return

    // Finde Section der Unit
    const section = playground.find(e => e.UnitID === active.id)?.Section
    if (!section) return

    const oldIndex = playground.findIndex(e => e.UnitID === active.id)
    const newIndex = playground.findIndex(e => e.UnitID === over.id)

    const reordered = arrayMove(playground, oldIndex, newIndex)
    const withUpdatedOrder = reordered.map((e, i) => ({ ...e, Order: i + 1 }))
    setPlayground(withUpdatedOrder)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {Object.entries(sections).map(([section, entries]) => (
        <div key={section}>
          <h3>{section}</h3>
          <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={entries.map(e => e.UnitID)} strategy={verticalListSortingStrategy}>
              {entries.map(e => (
                <SortableItem key={e.UnitID} id={e.UnitID}>
                  <div style={{
                    background: '#333',
                    padding: '0.5rem 1rem',
                    margin: '0.25rem 0',
                    borderRadius: '6px',
                    color: '#fff',
                    fontSize: '0.9rem'
                  }}>
                    {e.UnitID} – {e.Section} / {e.Subsection}
                  </div>
                </SortableItem>
              ))}
            </SortableContext>
          </DndContext>
        </div>
      ))}
    </div>
  )
}
