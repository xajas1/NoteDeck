import React, { useState, useEffect } from 'react'
import axios from 'axios'

const TexSnipTable = ({ units }) => {
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
    if (Array.isArray(units)) {
      setLocalUnits(units)
    }
  }, [units])

  const handleChange = (index, field, value) => {
    const updated = [...localUnits]
    updated[index][field] = value
    setLocalUnits(updated)

    axios.post('http://localhost:8000/update-unit', {
      UnitID: updated[index].UnitID,
      field,
      value
    }).then(res => {
      console.log("✅ Update erfolgreich:", res.data)
    }).catch(err => {
      console.error("❌ Fehler beim Update:", err)
    })
  }

  const getUniqueValues = (key) => {
    return Array.from(new Set(localUnits.map(u => u[key] ?? ""))).sort()
  }

  const isSubstantiveBody = (body) => {
    const trimmed = (body ?? "").trim()
    return trimmed.length > 10 && !trimmed.startsWith("%") && !/^%|\\%|\\todo/i.test(trimmed)
  }

  const filteredUnits = localUnits.filter(u => {
    return (
      (filter.Subject === "" || u.Subject === filter.Subject) &&
      (filter.Topic === "" || u.Topic === filter.Topic) &&
      (filter.CTyp === "" || u.CTyp === filter.CTyp) &&
      (filter.Body === "all" || (filter.Body === "yes" ? isSubstantiveBody(u.Body) : !isSubstantiveBody(u.Body)))
    )
  })

  const cellStyle = { padding: "4px 6px", fontSize: "0.75rem" }
  const metricCellStyle = { ...cellStyle, textAlign: "center" }
  const metricInputStyle = { width: "3.5rem", fontSize: "0.75rem", textAlign: "center" }

  return (
    <div style={{ marginTop: "2rem" }}>
      <h2 style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>Units dieser Quelle</h2>

      {/* Filterleiste */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", fontSize: "0.75rem" }}>
        <label>
          Subject:
          <select value={filter.Subject} onChange={e => setFilter({ ...filter, Subject: e.target.value })}>
            <option value="">(alle)</option>
            {getUniqueValues("Subject").map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label>
          Topic:
          <select value={filter.Topic} onChange={e => setFilter({ ...filter, Topic: e.target.value })}>
            <option value="">(alle)</option>
            {getUniqueValues("Topic").map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </label>
        <label>
          CTyp:
          <select value={filter.CTyp} onChange={e => setFilter({ ...filter, CTyp: e.target.value })}>
            <option value="">(alle)</option>
            {getUniqueValues("CTyp").map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label>
          Body:
          <select value={filter.Body} onChange={e => setFilter({ ...filter, Body: e.target.value })}>
            <option value="all">(alle)</option>
            <option value="yes">✅ vorhanden</option>
            <option value="no">❌ fehlt</option>
          </select>
        </label>
      </div>

      {/* Spaltensteuerung */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", fontSize: "0.75rem", marginBottom: "1rem" }}>
        {Object.keys(visibleColumns).map(col => (
          <label key={col}>
            <input
              type="checkbox"
              checked={visibleColumns[col]}
              onChange={() => setVisibleColumns(prev => ({
                ...prev,
                [col]: !prev[col]
              }))}
            />{" "}
            {col}
          </label>
        ))}
      </div>

      {/* Tabelle */}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
        <thead>
          <tr style={{ backgroundColor: "#222" }}>
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
              {visibleColumns.UnitID && <td style={cellStyle}>{u.UnitID}</td>}
              {visibleColumns.Subject && <td style={cellStyle}>{u.Subject}</td>}
              <td style={cellStyle}>{u.Topic}</td>
              <td style={cellStyle}>{u.CTyp}</td>
              <td style={cellStyle}>{u.Content}</td>

              {visibleColumns.Layer && (
                <td style={metricCellStyle}>
                  <input style={metricInputStyle} value={u.Layer ?? ""} onChange={e => handleChange(i, 'Layer', e.target.value)} />
                </td>
              )}
              {visibleColumns.Comp && (
                <td style={metricCellStyle}>
                  <input style={metricInputStyle} value={u.Comp ?? ""} onChange={e => handleChange(i, 'Comp', e.target.value)} />
                </td>
              )}
              {visibleColumns.RelInt && (
                <td style={metricCellStyle}>
                  <input style={metricInputStyle} value={u.RelInt ?? ""} onChange={e => handleChange(i, 'RelInt', e.target.value)} />
                </td>
              )}
              {visibleColumns.RelId && (
                <td style={metricCellStyle}>
                  <input style={metricInputStyle} value={u.RelId ?? ""} onChange={e => handleChange(i, 'RelId', e.target.value)} />
                </td>
              )}
              {visibleColumns.Cont && (
                <td style={metricCellStyle}>
                  <input style={metricInputStyle} value={u.Cont ?? ""} onChange={e => handleChange(i, 'Cont', e.target.value)} />
                </td>
              )}
              {visibleColumns.Cint && (
                <td style={metricCellStyle}>
                  <input style={metricInputStyle} value={u.Cint ?? ""} onChange={e => handleChange(i, 'Cint', e.target.value)} />
                </td>
              )}
              {visibleColumns.CID && (
                <td style={metricCellStyle}>
                  <input style={metricInputStyle} value={u.CID ?? ""} onChange={e => handleChange(i, 'CID', e.target.value)} />
                </td>
              )}

              <td style={{ textAlign: "center", fontSize: "0.9rem" }}>
                {isSubstantiveBody(u.Body) ? "✅" : "❌"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default TexSnipTable
