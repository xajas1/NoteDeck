import { useDraggable } from '@dnd-kit/core'
import { useState } from 'react'

export default function TreePlaygroundView({
  playground,
  units,
  structure,
  selectedUIDs,
  setSelectedUIDs,
  lastSelectedIndex,
  setLastSelectedIndex,
  setPlayground
}) {
  const [filterCTyp, setFilterCTyp] = useState('')
  const [filterLitID, setFilterLitID] = useState('')
  const [expandedSubjects, setExpandedSubjects] = useState(new Set())
  const [expandedTopics, setExpandedTopics] = useState({})
  const [expandedSources, setExpandedSources] = useState({})

  const getFullUnitByUID = (uid) => {
    const unit = units.find(u => u.UID === uid)
    if (!unit) {
      console.warn(`❗ Unit not found for UID: ${uid}`)
    }
    return unit
  }

  const isInEditor = (uid) => {
    return structure.some(section =>
      section.subsections.some(sub => sub.unitUIDs.includes(uid))
    )
  }
  

  const grouped = {}
  for (const entry of playground) {
    const full = getFullUnitByUID(entry.UID)
    if (!full) continue
    if (filterCTyp && full.CTyp !== filterCTyp) continue
    if (filterLitID && full.LitID !== filterLitID) continue

    const subject = full.Subject || '⟨Ohne Subject⟩'
    const topic = full.Topic || '⟨Ohne Topic⟩'
    const source = full.LitID || '⟨Ohne Quelle⟩'

    grouped[subject] ??= {}
    grouped[subject][topic] ??= {}
    grouped[subject][topic][source] ??= []
    grouped[subject][topic][source].push(full.UID)
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

  const toggleSource = (subject, topic, source) => {
    const key = `${subject}/${topic}`
    const next = { ...expandedSources }
    const current = new Set(next[key] || [])
    current.has(source) ? current.delete(source) : current.add(source)
    next[key] = current
    setExpandedSources(next)
  }

  const toggleSelection = (uid, index, shift = false) => {
    setSelectedUIDs(prev => {
      const next = new Set(prev)
      if (shift && lastSelectedIndex !== null) {
        const start = Math.min(lastSelectedIndex, index)
        const end = Math.max(lastSelectedIndex, index)
        for (let i = start; i <= end; i++) {
          next.add(playground[i].UID)
        }
      } else {
        if (next.has(uid)) next.delete(uid)
        else next.add(uid)
        setLastSelectedIndex(index)
      }
      return next
    })
  }

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
            fontSize: '0.68rem',
            marginRight: '1rem'
          }}
        >
          <>
          <option value="">— Alle —</option>
          {[
            ["DEF", "Definitionen"],
            ["PROP", "Propositionen"],
            ["THEO", "Theoreme"],
            ["LEM", "Lemmata"],
            ["KORO", "Korollare"],
            ["REM", "Bemerkungen"],
            ["OTH", "Sonstiges"],
            ["PROOF", "Beweise"],
            ["EXA", "Beispiele"],
            ["STUD", "Studienfragen"],
            ["CONC", "Konzepte"],
            ["EXE", "Übungen"],
            ["MOT", "Motivation"]
          ].map(([val, label]) => (
            <option key={val} value={val}>{label}</option>
          ))}
        </>
        </select>

        <label style={{ marginRight: '0.4rem' }}>Filter by LitID:</label>
        <select
          value={filterLitID}
          onChange={(e) => setFilterLitID(e.target.value)}
          style={{
            backgroundColor: '#1e1e1e',
            color: '#eee',
            border: '1px solid #444',
            padding: '0.15rem 0.4rem',
            borderRadius: '4px',
            fontSize: '0.68rem'
          }}
        >
          <option value="">— Alle Quellen —</option>
          {[...new Set(units.map(u => u.LitID).filter(Boolean))].map(id => (
            <option key={id} value={id}>{id}</option>
          ))}
        </select>
      </div>

      {Object.entries(grouped).map(([subject, topics]) => (
        <div key={subject}>
          <div style={styles.subject} onClick={() => toggleSubject(subject)}>
            <span style={{ cursor: 'pointer' }}>
              {expandedSubjects.has(subject) ? '▼' : '▶'} {subject}
            </span>
          </div>
          {expandedSubjects.has(subject) && Object.entries(topics).map(([topic, sources]) => (
            <div key={topic} style={{ paddingLeft: '0.8rem' }}>
              <div style={styles.topic} onClick={() => toggleTopic(subject, topic)}>
                <span style={{ cursor: 'pointer' }}>
                  {(expandedTopics[subject]?.has(topic)) ? '▼' : '▶'} {topic}
                </span>
              </div>
              {expandedTopics[subject]?.has(topic) && Object.entries(sources).map(([source, uids]) => {
                const key = `${subject}/${topic}`
                const isSourceOpen = expandedSources[key]?.has(source)
                return (
                  <div key={source} style={{ paddingLeft: '1rem' }}>
                    <div style={{ fontSize: '0.66rem', color: '#aaa', fontStyle: 'italic', cursor: 'pointer' }}
                      onClick={() => toggleSource(subject, topic, source)}>
                      {isSourceOpen ? '▼' : '▶'} {source}
                    </div>
                    {isSourceOpen && (
                      <ul style={styles.ul}>
                        {uids.map((uid) => {
                          const unit = getFullUnitByUID(uid)
                          if (!unit) return null
                          const index = playground.findIndex(p => p.UID === uid)
                          return (
                            <DraggableLine
                              key={uid}
                              uid={uid}
                              ctyp={unit?.CTyp}
                              name={unit?.Content}
                              unitID={unit?.UnitID}
                              isSelected={selectedUIDs.has(uid)}
                              isInEditor={isInEditor(uid)}
                              selectedUIDs={selectedUIDs}
                              onClick={(e) => toggleSelection(uid, index, e.shiftKey)}
                              setSelectedUIDs={setSelectedUIDs}
                              setPlayground={setPlayground}
                            />
                          )
                        })}
                      </ul>
                    )}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

function DraggableLine({ uid, ctyp, name, unitID, isSelected, isInEditor, onClick, selectedUIDs, setSelectedUIDs, setPlayground }) {
  const draggedUIDs = isSelected && selectedUIDs.size > 1
    ? Array.from(selectedUIDs)
    : [uid]

  const { attributes, listeners, setNodeRef } = useDraggable({
    id: `__drop__${uid}`,
    data: {
      type: 'unit',
      draggedIDs: draggedUIDs
    }
  })

  const handleRemove = (e) => {
    e.stopPropagation()
    setSelectedUIDs(prev => {
      const next = new Set(prev)
      next.delete(uid)
      return next
    })
    setPlayground(prev => prev.filter(p => p.UID !== uid))
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
        backgroundColor: isSelected
        ? '#336b9a22'
        : isInEditor
          ? 'rgba(100, 180, 255, 0.15)'
          : 'transparent',
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
        <strong>{unitID}</strong>: <span style={{ color: '#bbb' }}>{name}</span>
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
