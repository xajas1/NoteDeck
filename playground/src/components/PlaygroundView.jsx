export default function PlaygroundView({ playground, setPlayground }) {
    const handleChange = (uid, key, value) => {
      const updated = playground.map(u =>
        u.UnitID === uid ? { ...u, [key]: value } : u
      )
      setPlayground(updated)
    }
  
    return (
      <div style={{ padding: '1rem' }}>
        <h2>🧪 Playground</h2>
        {playground.length === 0 ? (
          <p>Keine Units ausgewählt.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>#</th>
                <th style={{ textAlign: 'left' }}>UnitID</th>
                <th style={{ textAlign: 'left' }}>Section</th>
                <th style={{ textAlign: 'left' }}>Subsection</th>
              </tr>
            </thead>
            <tbody>
              {playground
                .sort((a, b) => a.Order - b.Order)
                .map((unit, index) => (
                  <tr key={unit.UnitID}>
                    <td>{index + 1}</td>
                    <td><code>{unit.UnitID}</code></td>
                    <td>
                      <input
                        type="text"
                        value={unit.Section}
                        onChange={e =>
                          handleChange(unit.UnitID, "Section", e.target.value)
                        }
                        placeholder="z.B. Einführung"
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={unit.Subsection}
                        onChange={e =>
                          handleChange(unit.UnitID, "Subsection", e.target.value)
                        }
                        placeholder="z.B. Definition"
                      />
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        )}
      </div>
    )
  }
  