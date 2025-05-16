// src/components/UnitList.jsx
export function UnitList({ units }) {
    return (
      <div style={{ padding: '1rem' }}>
        <h2>📦 Alle Content Units</h2>
        <ul>
          {units.map(unit => (
            <li key={unit.UnitID}>
              <strong>{unit.UnitID}</strong>: {unit.Content}
            </li>
          ))}
        </ul>
      </div>
    );
  }
  