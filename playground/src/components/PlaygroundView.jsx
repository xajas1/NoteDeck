// PlaygroundGrouped.jsx
import { useMemo } from 'react'
import { DndContext } from '@dnd-kit/core'
import { arrayMove } from '@dnd-kit/sortable'
import PlaygroundSection from './PlaygroundSection'
import SortableItem from './SortableItemWrapper'

const itemStyle = {
  background: '#2a2a2a',
  padding: '0.5rem 1rem',
  borderRadius: '6px',
  color: '#eee',
  fontSize: '0.9rem',
  display: 'flex',
  justifyContent: 'space-between',
}

export default function PlaygroundGrouped({ playground, setPlayground }) {
  const sections = useMemo(() => {
    const grouped = {}
    for (const entry of playground) {
      const key = entry.Section || '(keine Section)'
      if (!grouped[key]) grouped[key] = []
      grouped[key].push(entry)
    }
    return grouped
  }, [playground])

  const handleDragEnd = ({ active, over }) => {
    if (!over) return

    const activeData = active.data.current
    const overData   = over.data.current

    if (activeData?.type !== 'unit') return

    const unitID   = active.id
    const fromSec  = activeData.fromSection
    const toSec    =
      overData?.type === 'section'
        ? over.id
        : overData?.fromSection

    if (!toSec) return

    const srcList = [...(sections[fromSec] || [])]
    const dstList = fromSec === toSec ? srcList : [...(sections[toSec] || [])]

    const movingIdx = srcList.findIndex(u => u.UnitID === unitID)
    const moving    = srcList.splice(movingIdx, 1)[0]
    if (!moving) return

    const insertAt =
      overData?.type === 'unit'
        ? dstList.findIndex(u => u.UnitID === over.id)
        : dstList.length

    dstList.splice(insertAt, 0, { ...moving, Section: toSec })

    const renumber = arr => arr.map((u, i) => ({ ...u, Order: i + 1 }))
    const allUpdated = renumber(fromSec === toSec ? dstList : srcList)
      .concat(renumber(fromSec === toSec ? [] : dstList))

    const updatedIDs = new Set(allUpdated.map(u => u.UnitID))

    const next = playground
      .filter(u => !updatedIDs.has(u.UnitID))
      .concat(allUpdated)

    setPlayground(next)
  }

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', padding: '1rem' }}>
        {Object.entries(sections).map(([section, entries]) => (
          <PlaygroundSection
            key={`section-${section}`}
            sectionID={section}
            title={section}
            itemIDs={entries.map(u => u.UnitID)}
          >
            {entries.map((e) => (
              <SortableItem key={`unit-${section}-${e.UnitID}`} id={e.UnitID} sectionID={section}>
                <div style={itemStyle}>
                  <span>{e.UnitID}</span>
                  <span style={{ opacity: 0.7 }}>{e.Section} / {e.Subsection}</span>
                </div>
              </SortableItem>
            ))}
          </PlaygroundSection>
        ))}
      </div>
    </DndContext>
  )
}
