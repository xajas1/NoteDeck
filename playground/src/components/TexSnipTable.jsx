import React, { useState, useEffect } from 'react'
import axios from 'axios'

const TexSnipTable = ({ units, onJumpToUnit }) => {
  const [localUnits, setLocalUnits] = useState([])
  const [filter, setFilter] = useState({
    Subject: "",
    Topic: "",
    CTyp: "",
    Body: "all"
  })

  const [visibleColumns, setVisibleColumns] = useState({
    UnitID: true,
    Subject: true,
    Layer: true,
    Comp: true,
    RelInt: true,
    RelId: true,
    Cont: true,
    Cint: true,
    CID: true,
  })

  useEffect(() => {
    if (Array.isArray(units)) setLocalUnits(units)
  }, [units])

  const handleChange = (index, field, value) => {
    const updated = [...localUnits]
    updated[index][field] = value
    setLocalUnits(updated)

    axios.post('http://localhost:8000/update-unit', {
      UnitID: updated[index].UnitID,
      field,
      value
    }).then(res => console.log("✅ Update:", res.data))
      .catch(err => console.error("❌ Fehler:", err))
  }

  const getUniqueValues = (key) => {
    return Array.from(new Set(localUnits.map(u => u[key] ?? ""))).sort()
  }

  const isSubstantiveBody = (body) => {
    const trimmed = (body ?? "").trim()
    return trimmed.length > 10 && !trimmed.startsWith("%") && !/^%|\\%|\\todo/i.test(trimmed)
  }

  const filteredUnits = localUnits.filter(u =>
    (filter.Subject === "" || u.Subject === filter.Subject) &&
    (filter.Topic === "" || u.Topic === filter.Topic) &&
    (filter.CTyp === "" || u.CTyp === filter.CTyp) &&
    (filter.Body === "all" || (filter.Body === "yes" ? isSubstantiveBody(u.Body) : !isSubstantiveBody(u.Body)))
  )

  const cellStyle = { padding: "2px 4px", fontSize: "0.7rem" }
  const metricCellStyle = { ...cellStyle, textAlign: "center" }
  const metricInputStyle = { width: "3rem", fontSize: "0.7rem", textAlign: "center", padding: "1px 3px" }

  return (
    <div style={{ padding: "0.5rem", display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.8rem", marginBottom: "0.5rem", fontSize: "0.75rem" }}>
        {["Subject", "Topic", "CTyp", "Body"].map((f) => (
          <label key={f}>
            {f}:
            <select
              value={filter[f]}
              onChange={e => setFilter({ ...filter, [f]: e.target.value })}
              style={{ fontSize: "0.75rem", marginLeft: "0.2rem" }}
            >
              {f !== "Body"
                ? <>
                    <option value="">(alle)</option>
                    {getUniqueValues(f).map(v => <option key={v} value={v}>{v}</option>)}
                  </>
                : <>
                    <option value="all">(alle)</option>
                    <option value="yes">✅</option>
                    <option value="no">❌</option>
                  </>
              }
            </select>
          </label>
        ))}
        <span style={{ marginLeft: "auto", fontSize: "0.7rem", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          {Object.keys(visibleColumns).map(col => (
            <label key={col}>
              <input
                type="checkbox"
                checked={visibleColumns[col]}
                onChange={() => setVisibleColumns(prev => ({ ...prev, [col]: !prev[col] }))}
              /> {col}
            </label>
          ))}
        </span>
      </div>

      <div style={{ flex: 1, overflowY: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
          <thead>
            <tr style={{ backgroundColor: "#222" }}>
              <th style={cellStyle}></th>
              {visibleColumns.UnitID && <th style={cellStyle}>UnitID</th>}
              {visibleColumns.Subject && <th style={cellStyle}>Subject</th>}
              <th style={cellStyle}>Topic</th>
              <th style={cellStyle}>CTyp</th>
              <th style={cellStyle}>Content</th>
              {visibleColumns.Layer && <th style={metricCellStyle}>Layer</th>}
              {visibleColumns.Comp && <th style={metricCellStyle}>Comp</th>}
              {visibleColumns.RelInt && <th style={metricCellStyle}>RelInt</th>}
              {visibleColumns.RelId && <th style={metricCellStyle}>RelId</th>}
              {visibleColumns.Cont && <th style={metricCellStyle}>Cont</th>}
              {visibleColumns.Cint && <th style={metricCellStyle}>Cint</th>}
              {visibleColumns.CID && <th style={metricCellStyle}>CID</th>}
              <th style={cellStyle}>Body?</th>
            </tr>
          </thead>
          <tbody>
            {filteredUnits.map((u, i) => (
              <tr key={u.UnitID} style={{ borderTop: "1px solid #444" }}>
                <td style={cellStyle}>
                  <button
                    onClick={() => onJumpToUnit?.({ unitID: u.UnitID, litID: u.LitID })}
                    title="Im Editor anzeigen"
                    style={{ fontSize: "0.8rem", padding: "0 4px" }}
                  >
                    🔍
                  </button>
                </td>
                {visibleColumns.UnitID && <td style={cellStyle}>{u.UnitID}</td>}
                {visibleColumns.Subject && <td style={cellStyle}>{u.Subject}</td>}
                <td style={cellStyle}>{u.Topic}</td>
                <td style={cellStyle}>{u.CTyp}</td>
                <td style={cellStyle}>{u.Content}</td>
                {visibleColumns.Layer && <td style={metricCellStyle}><input style={metricInputStyle} value={u.Layer ?? ""} onChange={e => handleChange(i, 'Layer', e.target.value)} /></td>}
                {visibleColumns.Comp && <td style={metricCellStyle}><input style={metricInputStyle} value={u.Comp ?? ""} onChange={e => handleChange(i, 'Comp', e.target.value)} /></td>}
                {visibleColumns.RelInt && <td style={metricCellStyle}><input style={metricInputStyle} value={u.RelInt ?? ""} onChange={e => handleChange(i, 'RelInt', e.target.value)} /></td>}
                {visibleColumns.RelId && <td style={metricCellStyle}><input style={metricInputStyle} value={u.RelId ?? ""} onChange={e => handleChange(i, 'RelId', e.target.value)} /></td>}
                {visibleColumns.Cont && <td style={metricCellStyle}><input style={metricInputStyle} value={u.Cont ?? ""} onChange={e => handleChange(i, 'Cont', e.target.value)} /></td>}
                {visibleColumns.Cint && <td style={metricCellStyle}><input style={metricInputStyle} value={u.Cint ?? ""} onChange={e => handleChange(i, 'Cint', e.target.value)} /></td>}
                {visibleColumns.CID && <td style={metricCellStyle}><input style={metricInputStyle} value={u.CID ?? ""} onChange={e => handleChange(i, 'CID', e.target.value)} /></td>}
                <td style={{ textAlign: "center" }}>{isSubstantiveBody(u.Body) ? "✅" : "❌"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default TexSnipTable
