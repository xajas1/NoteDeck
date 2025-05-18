import { useMemo } from "react"

function UnitFilter({ units, filters, setFilters }) {
  const subjects = useMemo(() => [...new Set(units.map(u => u.Subject))], [units])
  const topics   = useMemo(() => [...new Set(units.map(u => u.Topic))], [units])
  const ctypes   = useMemo(() => [...new Set(units.map(u => u.CTyp))], [units])

  function handleChange(field, value) {
    setFilters(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div style={{ marginBottom: "1rem" }}>
      <label>
        Subject:&nbsp;
        <select value={filters.Subject} onChange={e => handleChange("Subject", e.target.value)}>
          <option value="">(alle)</option>
          {subjects.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </label>
      &nbsp;&nbsp;
      <label>
        Topic:&nbsp;
        <select value={filters.Topic} onChange={e => handleChange("Topic", e.target.value)}>
          <option value="">(alle)</option>
          {topics.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </label>
      &nbsp;&nbsp;
      <label>
        Typ:&nbsp;
        <select value={filters.CTyp} onChange={e => handleChange("CTyp", e.target.value)}>
          <option value="">(alle)</option>
          {ctypes.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </label>
    </div>
  )
}

export default UnitFilter
