import { useDraggable } from '@dnd-kit/core'
import { useState } from 'react'

export default function TreePlaygroundView({
  playground,
  units,
  selectedIDs,
  setSelectedIDs,
  lastSelectedIndex,
  setLastSelectedIndex
}) {
  const [filterCTyp, setFilterCTyp] = useState('')  // leere Auswahl = kein Filter

  const getFullUnitByID = (id) => units.find(u => u.UnitID === id)

  const grouped = {}
  for (const unit of playground) {
    const full = getFullUnitByID(unit.UnitID)
    if (!full) continue
    if (filterCTyp && full.CTyp !== filterCTyp) continue  // Filter aktiv

    const subject = full.Subject || '⟨Ohne Subject⟩'
    const topic = full.Topic || '⟨Ohne Topic⟩'
    if (!grouped[subject]) grouped[subject] = {}
    if (!grouped[subject][topic]) grouped[subject][topic] = []
    grouped[subject][topic].push(unit.UnitID)
  }

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
        if (next.has(uid)) next.delete(uid)
        else next.add(uid)
        setLastSelectedIndex(index)
      }
      return next
    })
  }

  let globalIndex = 0

  return (
    <div style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: '#eee' }}>
      {/* 🔍 Filter */}
      <div style={{ marginBottom: '0.8rem' }}>
        <label style={{ marginRight: '0.5rem' }}>Filter by CTyp:</label>
        <select
          value={filterCTyp}
          onChange={(e) => setFilterCTyp(e.target.value)}
          style={{
            backgroundColor: '#1e1e1e',
            color: '#eee',
            border: '1px solid #444',
            padding: '0.2rem 0.4rem',
            borderRadius: '4px',
            fontSize: '0.82rem'
          }}
        >
          <option value="">— Alle —</option>
          <option value="DEF">Definitionen</option>
          <option value="PROP">Propositionen</option>
          <option value="LEM">Lemmata</option>
          <option value="THEO">Theoreme</option>
          <option value="EXA">Beispiele</option>
          <option value="REM">Bemerkungen</option>
          <option value="STUD">Studienfragen</option>
        </select>
      </div>

      {/* 🧩 Gruppenanzeige */}
      {Object.entries(grouped).map(([subject, topics]) => (
        <div key={subject}>
          <div style={styles.subject}>{subject}</div>
          {Object.entries(topics).map(([topic, ids]) => (
            <div key={topic} style={{ paddingLeft: '0.8rem' }}>
              <div style={styles.topic}>{topic}</div>
              <ul style={styles.ul}>
                {ids.map((uid) => {
                  const unit = getFullUnitByID(uid)
                  const index = globalIndex++
                  return (
                    <DraggableLine
                      key={uid}
                      uid={uid}
                      ctyp={unit?.CTyp}
                      name={unit?.Content}
                      isSelected={selectedIDs.has(uid)}
                      onClick={(e) => toggleSelection(uid, index, e.shiftKey)}
                    />
                  )
                })}
              </ul>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

function DraggableLine({ uid, ctyp, name, isSelected, onClick }) {
  const { attributes, listeners, setNodeRef } = useDraggable({
    id: `__drop__${uid}`,
    data: {
      type: 'unit',
      draggedIDs: [uid]
    }
  })

  return (
    <li
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      onClick={onClick}
      style={{
        cursor: 'grab',
        padding: '0.1rem 0.3rem',
        backgroundColor: isSelected ? '#2a2a2a' : 'transparent',
        borderLeft: isSelected ? '3px solid #4fc3f7' : '3px solid transparent',
        fontSize: '0.82rem',
        lineHeight: '1.2rem'
      }}
    >
      <span style={{ fontWeight: 'bold', color: '#7dd3fc' }}>[{ctyp}]</span>{' '}
      <strong>{uid}</strong>: <span style={{ color: '#bbb' }}>{name}</span>
    </li>
  )
}

const styles = {
  subject: {
    fontWeight: 'bold',
    fontSize: '0.85rem',
    marginTop: '0.7rem',
  },
  topic: {
    fontWeight: 'bold',
    fontSize: '0.82rem',
    marginTop: '0.2rem',
    color: '#ddd'
  },
  ul: {
    listStyle: 'none',
    paddingLeft: '0.8rem',
    margin: 0
  }
}
