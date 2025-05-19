// playground/src/components/TreePlaygroundView.jsx
import { useDraggable } from '@dnd-kit/core'
import { useState } from 'react'

export default function TreePlaygroundView({
  playground,
  units,
  selectedIDs,
  setSelectedIDs,
  lastSelectedIndex,
  setLastSelectedIndex,
  setPlayground
}) {
  const [filterCTyp, setFilterCTyp] = useState('')
  const [expandedSubjects, setExpandedSubjects] = useState(new Set())
  const [expandedTopics, setExpandedTopics] = useState({})

  const getFullUnitByID = (id) => units.find(u => u.UnitID === id)

  const grouped = {}
  for (const unit of playground) {
    const full = getFullUnitByID(unit.UnitID)
    if (!full) continue
    if (filterCTyp && full.CTyp !== filterCTyp) continue

    const subject = full.Subject || '⟨Ohne Subject⟩'
    const topic = full.Topic || '⟨Ohne Topic⟩'
    if (!grouped[subject]) grouped[subject] = {}
    if (!grouped[subject][topic]) grouped[subject][topic] = []
    grouped[subject][topic].push(unit.UnitID)
  }

  const toggleSubject = (subject) => {
    const next = new Set(expandedSubjects)
    next.has(subject) ? next.delete(subject) : next.add(subject)
    setExpandedSubjects(next)
  }

  const toggleTopic = (subject, topic) => {
    const next = { ...expandedTopics }
    const current = new Set(next[subject] || [])
    current.has(topic) ? current.delete(topic) : current.add(topic)
    next[subject] = current
    setExpandedTopics(next)
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
    <div style={{ fontFamily: 'monospace', fontSize: '0.68rem', color: '#eee' }}>
      <div style={{ marginBottom: '0.5rem' }}>
        <label style={{ marginRight: '0.4rem' }}>Filter by CTyp:</label>
        <select
          value={filterCTyp}
          onChange={(e) => setFilterCTyp(e.target.value)}
          style={{
            backgroundColor: '#1e1e1e',
            color: '#eee',
            border: '1px solid #444',
            padding: '0.15rem 0.4rem',
            borderRadius: '4px',
            fontSize: '0.68rem'
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

      {Object.entries(grouped).map(([subject, topics]) => (
        <div key={subject}>
          <div style={styles.subject} onClick={() => toggleSubject(subject)}>
            <span style={{ cursor: 'pointer' }}>
              {expandedSubjects.has(subject) ? '▼' : '▶'} {subject}
            </span>
          </div>
          {expandedSubjects.has(subject) && Object.entries(topics).map(([topic, ids]) => (
            <div key={topic} style={{ paddingLeft: '0.8rem' }}>
              <div style={styles.topic} onClick={() => toggleTopic(subject, topic)}>
                <span style={{ cursor: 'pointer' }}>
                  {(expandedTopics[subject]?.has(topic)) ? '▼' : '▶'} {topic}
                </span>
              </div>
              {expandedTopics[subject]?.has(topic) && (
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
                        selectedIDs={selectedIDs}
                        onClick={(e) => toggleSelection(uid, index, e.shiftKey)}
                        setSelectedIDs={setSelectedIDs}
                        setPlayground={setPlayground}
                      />
                    )
                  })}
                </ul>
              )}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

function DraggableLine({ uid, ctyp, name, isSelected, onClick, selectedIDs, setSelectedIDs, setPlayground }) {
  const draggedIDs = isSelected && selectedIDs.size > 1
    ? Array.from(selectedIDs)
    : [uid]

  const { attributes, listeners, setNodeRef } = useDraggable({
    id: `__drop__${uid}`,
    data: {
      type: 'unit',
      draggedIDs
    }
  })

  const handleRemove = (e) => {
    e.stopPropagation()
    setSelectedIDs(prev => {
      const next = new Set(prev)
      next.delete(uid)
      return next
    })
    setPlayground(prev => prev.filter(p => p.UnitID !== uid))
  }

  return (
    <li
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      onClick={onClick}
      style={{
        cursor: 'grab',
        padding: '0rem 0.2rem',
        backgroundColor: isSelected ? '#2a2a2a' : 'transparent',
        borderLeft: isSelected ? '2px solid #4fc3f7' : '2px solid transparent',
        fontSize: '0.68rem',
        lineHeight: '0.95rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.02rem'
      }}
    >
      <span>
        <span style={{ fontWeight: 'bold', color: '#7dd3fc' }}>[{ctyp}]</span>{' '}
        <strong>{uid}</strong>: <span style={{ color: '#bbb' }}>{name}</span>
      </span>
      <button onClick={handleRemove} style={{
        background: 'transparent',
        color: '#60a5fa',
        border: 'none',
        cursor: 'pointer',
        marginLeft: '0.4rem',
        fontSize: '0.72rem',
        lineHeight: '1rem'
      }}>✕</button>
    </li>
  )
}

const styles = {
  subject: {
    fontWeight: 'bold',
    fontSize: '0.7rem',
    marginTop: '0.3rem',
    cursor: 'pointer',
  },
  topic: {
    fontWeight: 'bold',
    fontSize: '0.68rem',
    marginTop: '0.15rem',
    color: '#ddd',
    cursor: 'pointer'
  },
  ul: {
    listStyle: 'none',
    paddingLeft: '0.6rem',
    margin: 0
  }
}
