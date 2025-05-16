// PlaygroundList.jsx
import {
    DndContext,
    closestCenter,
    useSensor,
    useSensors,
    PointerSensor
  } from '@dnd-kit/core'
  
  import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    verticalListSortingStrategy,
    useSortable,
  } from '@dnd-kit/sortable'
  
  import { CSS } from '@dnd-kit/utilities'
  import { useState } from 'react'
  
  function SortableItem({ id, item, onChange }) {
    const {
      attributes,
      listeners,
      setNodeRef,
      transform,
      transition
    } = useSortable({ id })
  
    const style = {
      transform: CSS.Transform.toString(transform),
      transition,
      padding: '0.5rem',
      display: 'flex',
      gap: '1rem',
      alignItems: 'center',
      backgroundColor: '#2a2a2a',
      borderBottom: '1px solid #444',
      borderRadius: '4px'
    }
  
    return (
      <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
        <div style={{ width: 30 }}>{item.Order}</div>
        <div style={{ width: 120 }}>{item.UnitID}</div>
        <input
          style={{ flex: 1 }}
          value={item.Section}
          onChange={(e) => onChange(id, 'Section', e.target.value)}
          placeholder="z.B. Einführung"
        />
        <input
          style={{ flex: 1 }}
          value={item.Subsection}
          onChange={(e) => onChange(id, 'Subsection', e.target.value)}
          placeholder="z.B. Definition"
        />
      </div>
    )
  }
  
  export default function PlaygroundList({ playground, setPlayground }) {
    const sensors = useSensors(
      useSensor(PointerSensor)
    )
  
    const handleDragEnd = (event) => {
      const { active, over } = event
      if (active.id !== over?.id) {
        const oldIndex = playground.findIndex(e => e.UnitID === active.id)
        const newIndex = playground.findIndex(e => e.UnitID === over.id)
        const newItems = arrayMove(playground, oldIndex, newIndex)
        setPlayground(newItems.map((e, i) => ({ ...e, Order: i + 1 })))
      }
    }
  
    const handleChange = (id, key, value) => {
      setPlayground(prev =>
        prev.map(entry =>
          entry.UnitID === id ? { ...entry, [key]: value } : entry
        )
      )
    }
  
    return (
      <>
        <h3>🧪 Playground</h3>
        {playground.length === 0 ? (
          <p>Keine Units ausgewählt.</p>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={playground.map(entry => entry.UnitID)}
              strategy={verticalListSortingStrategy}
            >
              {playground.map(entry => (
                <SortableItem
                  key={entry.UnitID}
                  id={entry.UnitID}
                  item={entry}
                  onChange={handleChange}
                />
              ))}
            </SortableContext>
          </DndContext>
        )}
      </>
    )
  }
  