import { useState } from 'react'

export default function Sidebar({ units, playground, setPlayground }) {
  const [expanded, setExpanded] = useState(new Set())  // eingeklappte Topics

  const toggleExpand = (topic) => {
    const newExpanded = new Set(expanded)
    if (expanded.has(topic)) {
      newExpanded.delete(topic)
    } else {
      newExpanded.add(topic)
    }
    setExpanded(newExpanded)
  }

  const isSelected = (uid) => playground.some(p => p.UnitID === uid)

  const handleToggleUnit = (unit) => {
    if (isSelected(unit.UnitID)) {
      setPlayground(playground.filter(p => p.UnitID !== unit.UnitID))
    } else {
      setPlayground([
        ...playground,
        {
          UnitID: unit.UnitID,
          Name: unit.Content, // ✅ Name übernehmen
          Section: "",
          Subsection: "",
          Order: playground.length + 1
        }
      ])
    }
  }

  const handleToggleAll = (unitIDs) => {
    const allSelected = unitIDs.every(id => isSelected(id))

    if (allSelected) {
      setPlayground(playground.filter(p => !unitIDs.includes(p.UnitID)))
    } else {
      const unitsToAdd = units.filter(u => unitIDs.includes(u.UnitID) && !isSelected(u.UnitID))
      const newEntries = unitsToAdd.map((u, i) => ({
        UnitID: u.UnitID,
        Name: u.Content, // ✅ Name übernehmen
        Section: "",
        Subsection: "",
        Order: playground.length + i + 1
      }))
      setPlayground([...playground, ...newEntries])
    }
  }

  // Gruppiere Units nach Subject → Topic
  const grouped = {}
  for (const u of units) {
    if (!grouped[u.Subject]) grouped[u.Subject] = {}
    if (!grouped[u.Subject][u.Topic]) grouped[u.Subject][u.Topic] = []
    grouped[u.Subject][u.Topic].push(u)
  }

  return (
    <div style={{ padding: '1rem', width: '300px', backgroundColor: '#111', color: '#eee', fontSize: '0.9rem' }}>
      <h2>Inhalte</h2>
      {Object.entries(grouped).map(([subject, topics]) => {
        const allIdsInSubject = Object.values(topics).flat().map(u => u.UnitID)
        return (
          <div key={subject}>
            <label>
              <input
                type="checkbox"
                checked={allIdsInSubject.every(id => isSelected(id))}
                onChange={() => handleToggleAll(allIdsInSubject)}
              />
              <strong style={{ marginLeft: "0.5rem" }}>{subject}</strong>
            </label>
            <div style={{ paddingLeft: "1rem" }}>
              {Object.entries(topics).map(([topic, units]) => {
                const allIdsInTopic = units.map(u => u.UnitID)
                const isOpen = expanded.has(topic)
                return (
                  <div key={topic}>
                    <label>
                      <input
                        type="checkbox"
                        checked={allIdsInTopic.every(id => isSelected(id))}
                        onChange={() => handleToggleAll(allIdsInTopic)}
                      />
                      <span
                        style={{ cursor: "pointer", marginLeft: "0.5rem" }}
                        onClick={() => toggleExpand(topic)}
                      >
                        {isOpen ? "▼" : "▶"} {topic}
                      </span>
                    </label>
                    {isOpen && (
                      <ul style={{ listStyle: "none", paddingLeft: "1.5rem" }}>
                        {units.map(u => (
                          <li key={u.UnitID}>
                            <label>
                              <input
                                type="checkbox"
                                checked={isSelected(u.UnitID)}
                                onChange={() => handleToggleUnit(u)}
                              />
                              <span style={{ marginLeft: "0.5rem" }}>{u.UnitID}: {u.Content}</span>
                            </label>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
