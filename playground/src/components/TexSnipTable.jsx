import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const TexSnipTable = ({ units, onJumpToUnit, onStartReplaceMode }) => {
  const [localUnits, setLocalUnits] = useState([])
  const [topicIndexMap, setTopicIndexMap] = useState({})
  const [savedIndex, setSavedIndex] = useState(null)

  const [filter, setFilter] = useState({
    Subject: "",
    Topic: "",
    CTyp: "",
    Body: "all"
  })

  const [visibleColumns, setVisibleColumns] = useState({
    UnitID: true,
    Subject: true,
    ParentTopic: true,
    Layer: true,
    Comp: true,
    RelInt: true,
    RelId: true,
    Cont: true,
    Cint: true,
    CID: true,
  })

  const originalUnitsRef = useRef([])

// 🔁 Ref und lokale Units synchronisieren
useEffect(() => {
    if (Array.isArray(units)) {
      setLocalUnits(units)
  
      units.forEach((unit) => {
        const exists = originalUnitsRef.current.some(u => u.UnitID === unit.UnitID)
        if (!exists) {
          originalUnitsRef.current.push({ ...unit })
        }
      })
    }
  }, [units])
  
  // 🌐 TopicMap separat laden (nur einmal)
  useEffect(() => {
    axios.get("http://localhost:8000/topic-map")
      .then(res => setTopicIndexMap(res.data))
      .catch(err => console.error("Fehler beim Laden von /topic-map:", err))
  }, [])
  
  

  const getTopicIndex = (subject, topic) => {
    try {
      return topicIndexMap?.[subject]?.topics?.[topic]?.index?.toString().padStart(2, "0") ?? "XX"
    } catch {
      return "XX"
    }
  }

  const computeExpectedUnitID = (unit) => {
    const subject = unit.Subject?.trim();
    const litID = unit.LitID?.trim();
    const topicIndex = getTopicIndex(subject, unit.Topic?.trim());
  
    // Versuche, die laufende Nummer aus der aktuellen UnitID zu extrahieren:
    const parts = unit.UnitID?.split("-");
    const unitNumber = parts?.[3] ?? "??";
  
    return `${subject}-${litID}-${topicIndex}-${unitNumber}`;
  };
  
  const isRenameRelevant = (unit) => {
    // Wenn die erwartete ID bereits gleich der aktuellen ist: kein Rename nötig
    return unit.UnitID !== computeExpectedUnitID(unit);
  };
  


  const computePreviewID = (unit) => {
    const subject = unit.Subject?.trim() ?? "SUB"
    const source = unit.LitID?.trim() ?? "SRC"
    const topic = getTopicIndex(subject, unit.Topic?.trim())
    return `${subject}-${source}-${topic}-??`
  }

  const handleChange = (index, field, value) => {
    const updated = [...localUnits]
    updated[index][field] = value
    setLocalUnits(updated)
  
    // 🧠 ENV/Content Update
    if (field === "CTyp" || field === "Content") {
      axios.post('http://localhost:8000/update-env-or-content', {
        UnitID: updated[index].UnitID,
        Content: updated[index].Content,
        CTyp: updated[index].CTyp
      }).then(res => {
        console.log("✅ ENV/Content Update:", res.data)
        originalUnitsRef.current[index] = { ...updated[index] }
        setSavedIndex(index)
        setTimeout(() => setSavedIndex(null), 2000)
      }).catch(err => console.error("❌ Fehler (ENV/Content):", err))
    }
  
    // 🔁 Subject / Topic / LitID → rename-unit verwenden
    else if (["Subject", "Topic", "LitID"].includes(field)) {
      const newUnit = updated[index]
      const payload = {
        oldUnitID: newUnit.UnitID,
        Subject: newUnit.Subject,
        Topic: newUnit.Topic,
        LitID: newUnit.LitID,
        CTyp: newUnit.CTyp,
        Content: newUnit.Content,
        updatedFields: {
          Subject: newUnit.Subject,
          Topic: newUnit.Topic,
          ParentTopic: newUnit.ParentTopic,
          CTyp: newUnit.CTyp,
          Content: newUnit.Content
        }
      }
  
      axios.post("http://localhost:8000/rename-unit", payload)
        .then(res => {
          console.log("🔁 Rename ausgeführt:", res.data)
          updated[index].UnitID = res.data.newUnitID
          setLocalUnits(updated)
          setSavedIndex(index)
          setTimeout(() => setSavedIndex(null), 2000)
        })
        .catch(err => console.error("❌ Fehler (Rename):", err))
    }
  
    // ✅ Normale Felder
    else {
      axios.post('http://localhost:8000/update-unit', {
        UnitID: updated[index].UnitID,
        field,
        value
      }).then(res => console.log("✅ Update:", res.data))
        .catch(err => console.error("❌ Fehler:", err))
    }
  }
  

  const handleRename = async (index, oldUnitID, newUnitID) => {
    const updated = localUnits[index]
    await handleEnvOrContentUpdate(index)

    const payload = {
      oldUnitID,
      newUnitID,
      Subject: updated.Subject,
      Topic: updated.Topic,
      LitID: updated.LitID,
      CTyp: updated.CTyp,
      Content: updated.Content,
      updatedFields: {
        Subject: updated.Subject,
        Topic: updated.Topic,
        ParentTopic: updated.ParentTopic,
        CTyp: updated.CTyp,
        Content: updated.Content
      }
    }

    try {
      console.log("🔍 Payload für Rename:", payload)
      const res = await axios.post("http://localhost:8000/rename-unit", payload)
      console.log("🔁 Renamed:", res.data)
      const newLocalUnits = [...localUnits]
      newLocalUnits.splice(index, 1)
      newLocalUnits.push({ ...updated, UnitID: res.data.newUnitID })
      setLocalUnits(newLocalUnits)
      setSavedIndex(index)
      setTimeout(() => setSavedIndex(null), 2000)
    } catch (err) {
      console.error("❌ Fehler bei rename-unit:", err)
    }
  }

  const handleEnvOrContentUpdate = async (index) => {
    const updated = localUnits[index]
    const payload = {
      UnitID: updated.UnitID,
      Content: updated.Content,
      CTyp: updated.CTyp
    }
  
    try {
      console.log("📤 Update ENV/Content:", payload)
      const res = await axios.post("http://localhost:8000/update-env-or-content", payload)
      console.log("✅ ENV/Content aktualisiert:", res.data)
  
      // ✅ Update originalUnitsRef, damit Änderung nicht mehr als neu erkannt wird
      originalUnitsRef.current[index] = { ...updated }
  
      // ✅ Visualer Speicherindikator
      setSavedIndex(index)
      setTimeout(() => setSavedIndex(null), 2000)
  
    } catch (err) {
      console.error("❌ Fehler bei ENV/Content-Update:", err)
    }
  }
  

  const isCTypOrContentChanged = (unit) => {
    const original = originalUnitsRef.current.find(u => u.UnitID === unit.UnitID)
    if (!original) return false
    return original.Content !== unit.Content || original.CTyp !== unit.CTyp
  }
      
  
  
  
  const getUniqueValues = (key) => {
    const fullSet = [...originalUnitsRef.current, ...localUnits]
    return Array.from(new Set(
      fullSet.map(u => (u[key] ?? "").trim()).filter(v => v !== "")
    )).sort()
  }
  
  

  const isSubstantiveBody = (body) => {
    const trimmed = (body ?? "").trim()
    return trimmed.length > 10 && !trimmed.startsWith("%") && !/^%|\\%|\\todo/i.test(trimmed)
  }

const filteredUnits = localUnits.filter(u =>
    (filter.Subject === "" || u.Subject?.trim().toLowerCase() === filter.Subject.trim().toLowerCase()) &&
    (filter.Topic === "" || u.Topic === filter.Topic) &&
    (filter.CTyp === "" || u.CTyp === filter.CTyp) &&
    (filter.Body === "all" || (filter.Body === "yes" ? isSubstantiveBody(u.Body) : !isSubstantiveBody(u.Body)))
  )

  const cellStyle = { padding: "2px 4px", fontSize: "0.7rem" }
  const metricCellStyle = { ...cellStyle, textAlign: "center" }
  const metricInputStyle = { width: "3rem", fontSize: "0.7rem", textAlign: "center", padding: "1px 3px" }

  const buttonStyle = {
    fontSize: "0.6rem",
    padding: "0.2rem 0.3rem",
    border: "none",
    borderRadius: "3px",
    cursor: "pointer",
    backgroundColor: "#444",
    color: "white",
    minWidth: "1.5rem"
  }
  

  return (
    <div style={{ padding: "0.5rem", display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Filter und Sichtbarkeitsleiste */}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.8rem", marginBottom: "0.5rem", fontSize: "0.75rem" }}>
        {["Subject", "Topic", "CTyp", "Body"].map((f) => (
          <label key={f}>
            {f}:
            <select
              value={filter[f]}
              onChange={e => setFilter({ ...filter, [f]: e.target.value })}
              style={{ fontSize: "0.75rem", marginLeft: "0.2rem" }}
            >
              {f !== "Body" ? (
                <>
                  <option value="">(alle)</option>
                  {f === "CTyp"
                    ? [
                        "DEF", "PROP", "THEO", "LEM", "KORO", "REM",
                        "OTH", "PROOF", "EXA", "STUD", "CONC", "EXE", "MOT"
                        ].map(v => <option key={v} value={v}>{v}</option>)
                    : getUniqueValues(f).map(v => <option key={v} value={v}>{v}</option>)
                    }
                </>
              ) : (
                <>
                  <option value="all">(alle)</option>
                  <option value="yes">✅</option>
                  <option value="no">❌</option>
                </>
              )}
            </select>
          </label>
        ))}
        <span style={{ marginLeft: "auto", fontSize: "0.7rem", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          {Object.keys(visibleColumns).map(col => (
            <label key={col}>
              <input
                type="checkbox"
                checked={visibleColumns[col]}
                onChange={() =>
                  setVisibleColumns(prev => ({ ...prev, [col]: !prev[col] }))
                }
              />
              {col}
            </label>
          ))}
        </span>
      </div>
  
      {/* Tabellenansicht */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
            <thead>
            <tr style={{ backgroundColor: "#222" }}>
                <th style={cellStyle}>⚙️</th>
                {visibleColumns.UnitID ? <th style={cellStyle}>UnitID</th> : null}
                {visibleColumns.Subject ? <th style={cellStyle}>Subject</th> : null}
                <th style={cellStyle}>Topic</th>
                {visibleColumns.ParentTopic ? <th style={cellStyle}>ParentTopic</th> : null}
                <th style={cellStyle}>CTyp</th>
                <th style={cellStyle}>Content</th>
                {visibleColumns.Layer ? <th style={metricCellStyle}>Layer</th> : null}
                {visibleColumns.Comp ? <th style={metricCellStyle}>Comp</th> : null}
                {visibleColumns.RelInt ? <th style={metricCellStyle}>RelInt</th> : null}
                {visibleColumns.RelId ? <th style={metricCellStyle}>RelId</th> : null}
                {visibleColumns.Cont ? <th style={metricCellStyle}>Cont</th> : null}
                {visibleColumns.Cint ? <th style={metricCellStyle}>Cint</th> : null}
                {visibleColumns.CID ? <th style={metricCellStyle}>CID</th> : null}
                <th style={cellStyle}>Body?</th>
            </tr>
            </thead>

          <tbody>
            {filteredUnits.map((u, i) => (
              <tr key={u.UnitID} style={{ borderTop: "1px solid #444" }}>
                {/* Neue erste Spalte: Aktions-Buttons */}
                <td style={{ ...cellStyle, display: "flex", flexWrap: "wrap", gap: "0.15rem", justifyContent: "center" }}>
                  <button
                    onClick={() => onStartReplaceMode?.(u)}
                    title={isSubstantiveBody(u.Body) ? "Vorhandenen Body ersetzen" : "Body hinzufügen"}
                    style={{
                      ...buttonStyle,
                      backgroundColor: isSubstantiveBody(u.Body) ? "#775" : "#335"
                    }}
                  >
                    🔁
                  </button>
                  <button
                    onClick={() => onJumpToUnit?.({ unitID: u.UnitID, litID: u.LitID })}
                    title="Im Editor anzeigen"
                    style={buttonStyle}
                  >
                    🔍
                  </button>
                </td>
  
                {/* Alle restlichen Spalten (unverändert) */}
                {visibleColumns.UnitID && (
                  <td style={cellStyle}>
                    {u.UnitID}
                    {isRenameRelevant(u) && (
                      <>
                        <div style={{ fontSize: "0.65rem", color: "orange" }}>→ {computePreviewID(u)}</div>
                        <button
                          onClick={() => handleRename(i, u.UnitID, computePreviewID(u))}
                          style={{ ...buttonStyle, marginTop: "2px" }}
                        >
                          🔁 Speichern
                        </button>
                      </>
                    )}
                    {!isRenameRelevant(u) && isCTypOrContentChanged(u) && (
                      <button
                        onClick={() => handleEnvOrContentUpdate(i)}
                        style={{ ...buttonStyle, marginTop: "4px", backgroundColor: "#355" }}
                      >
                        ♻️ Update
                      </button>
                    )}
                    {savedIndex === i && (
                      <div style={{ fontSize: "0.65rem", color: "limegreen" }}>✅ gespeichert</div>
                    )}
                  </td>
                )}
                {visibleColumns.Subject && (
                  <td style={cellStyle}>
                    <input style={metricInputStyle} value={u.Subject ?? ""} onChange={e => handleChange(i, 'Subject', e.target.value)} />
                  </td>
                )}
                <td style={cellStyle}>
                  <input style={metricInputStyle} value={u.Topic ?? ""} onChange={e => handleChange(i, 'Topic', e.target.value)} />
                </td>
                {visibleColumns.ParentTopic && (
                  <td style={cellStyle}>
                    <input style={metricInputStyle} value={u.ParentTopic ?? ""} onChange={e => handleChange(i, 'ParentTopic', e.target.value)} />
                  </td>
                )}
                <td style={cellStyle}>
                    <select
                        value={u.CTyp ?? ""}
                        onChange={e => handleChange(i, 'CTyp', e.target.value)}
                        style={{ ...metricInputStyle, width: "6rem" }}>
                        <option value="">–</option>
                        {[
                        "DEF", "PROP", "THEO", "LEM", "KORO", "REM",
                        "OTH", "PROOF", "EXA", "STUD", "CONC", "EXE", "MOT"
                        ].map(ct => <option key={ct} value={ct}>{ct}</option>)}
                    </select>
                </td>
                <td style={cellStyle}>
                  <input style={{ ...metricInputStyle, width: "10rem" }} value={u.Content ?? ""} onChange={e => handleChange(i, 'Content', e.target.value)} />
                </td>
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
