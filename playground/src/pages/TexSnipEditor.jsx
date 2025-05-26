import React, {
    useEffect,
    useState,
    useRef,
    forwardRef,
    useImperativeHandle
  } from "react"
  import AceEditor from "react-ace"
  
  // Themes & Modes
  import "ace-builds/src-noconflict/theme-twilight"
  import "ace-builds/src-noconflict/mode-latex"
  
  // Ace-Setup
  import ace from "ace-builds/src-noconflict/ace"
  ace.config.set("basePath", "/ace")

  const TexSnipEditor = forwardRef(({ splitState, onMetaChange, onNewUnit }, ref) => {
    const [subject, setSubject] = useState("A")
    const [topic, setTopic] = useState("Ringe Basics")
    const [litID, setLitID] = useState("T12")
    const [ctyp, setCtyp] = useState("DEF")
    const [parentTopic, setParentTopic] = useState("Ringe")
    const [content, setContent] = useState("")
    const [body, setBody] = useState("")
  
    const [freezeSubject, setFreezeSubject] = useState(true)
    const [freezeTopic, setFreezeTopic] = useState(true)
    const [freezeParent, setFreezeParent] = useState(true)
    const [freezeLitID, setFreezeLitID] = useState(true)
  
    const [topicMap, setTopicMap] = useState({})
    const [projects, setProjects] = useState([])
    const [selectedProject, setSelectedProject] = useState("")
    const [response, setResponse] = useState(null)
    const aceRef = useRef(null)
  
    // For scrolling from table
    useImperativeHandle(ref, () => ({
      scrollToUnit(unitID) {
        const editor = aceRef.current?.editor
        if (!editor || !unitID) return
        const session = editor.getSession()
        const lines = session.getDocument().getAllLines()
        const lineIndex = lines.findIndex(line => line.includes(`{${unitID}}`))
        if (lineIndex !== -1) {
          editor.focus()
          editor.gotoLine(lineIndex + 1, 0, true)
          editor.scrollToLine(lineIndex, true, true)
        }
      }
    }))
  
    // Setup available projects and topicMap
    useEffect(() => {
      fetch("http://localhost:8000/topic-map").then(res => res.json()).then(setTopicMap)
      fetch("http://localhost:8000/available-sources").then(res => res.json()).then(setProjects)
    }, [])
  
    // Load snapshot data
    useEffect(() => {
      if (splitState?.sourceFile) {
        setSelectedProject(splitState.sourceFile)
        loadSourceByProject(splitState.sourceFile)
      }
      if (splitState?.snipMeta) {
        const m = splitState.snipMeta
        if (m.Subject) setSubject(m.Subject)
        if (m.Topic) setTopic(m.Topic)
        if (m.LitID) setLitID(m.LitID)
        if (m.Content) setContent(m.Content)
        if (m.ParentTopic) setParentTopic(m.ParentTopic)
        if (m.CTyp) setCtyp(m.CTyp)
      }
    }, [splitState])
  
    // Pass meta state upward
    useEffect(() => {
      if (onMetaChange) {
        onMetaChange({
          Subject: subject,
          Topic: topic,
          LitID: litID,
          CTyp: ctyp,
          ParentTopic: parentTopic,
          Content: content,
          selectedProject
        })
      }
    }, [subject, topic, litID, ctyp, parentTopic, content, selectedProject])
  
    // Inject custom highlight rules into ace
    useEffect(() => {
        ace.config.loadModule("ace/mode/latex_custom", (module) => {
          if (module && aceRef.current?.editor) {
            aceRef.current.editor.getSession().setMode(new module.Mode())
          } else {
            console.error("❌ Fehler beim Laden des benutzerdefinierten Latex-Modus.")
          }
        })
      }, [body])

    const topicExists = () =>
      topicMap[subject] && Object.keys(topicMap[subject].topics || {}).includes(topic)
  
    const ensureTopicExists = async () => {
      if (!topicExists()) {
        const res = await fetch("http://localhost:8000/add-topic", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ Subject: subject, Topic: topic, ParentTopic: parentTopic || null }),
        })
        const json = await res.json()
        setTopicMap(prev => {
          const updated = { ...prev }
          if (!updated[subject]) updated[subject] = { index: 99, topics: {} }
          updated[subject].topics[topic] = { index: json.index, parent: parentTopic || null }
          return updated
        })
      }
    }
  
    const handleSubmit = async () => {
      await ensureTopicExists()
      const editor = aceRef.current?.editor
      if (!editor) return
  
      const selectedText = editor.getSelectedText().trim()
      if (!selectedText) return
  
      const payload = {
        Subject: subject,
        Topic: topic,
        LitID: litID,
        CTyp: ctyp,
        Content: content,
        Body: selectedText,
        ParentTopic: parentTopic,
        project: selectedProject,
      }
  
      const res = await fetch("http://localhost:8000/snip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
  
      const json = await res.json()
      setResponse(json)
      if (json.unit && typeof onNewUnit === "function") {
        onNewUnit(json.unit)
      }
                 
  
      if (json.UnitID) {
        const wrappedText = `\\begin{${ctyp}}{${json.UnitID}}{${content}}\n${selectedText}\n\\end{${ctyp}}`
        const range = editor.getSelectionRange()
        editor.session.replace(range, wrappedText)
        setBody(editor.getValue())
      }
  
      if (!freezeSubject) setSubject("")
      if (!freezeTopic) setTopic("")
      if (!freezeParent) setParentTopic("")
      if (!freezeLitID) setLitID("")
    }
  
    const loadSourceByProject = async (project) => {
      const res = await fetch(`http://localhost:8000/load-source?project=${project}`)
      const json = await res.json()
      setBody(json.content || "")
    }
  
    const saveSource = async () => {
      await fetch("http://localhost:8000/save-source", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project: selectedProject, content: body }),
      })
    }
  
    useEffect(() => {
      const handleKeyDown = (e) => {
        const isCmd = e.metaKey || e.ctrlKey
        const isEnter = e.key === "Enter"
        if (isCmd && isEnter && !e.shiftKey && !e.altKey) {
          e.preventDefault()
          saveSource()
        } else if (isCmd && isEnter && e.shiftKey) {
          e.preventDefault()
          loadSourceByProject(selectedProject)
        } else if (e.altKey && isEnter) {
          e.preventDefault()
          handleSubmit()
        }
      }
  
      window.addEventListener("keydown", handleKeyDown)
      return () => window.removeEventListener("keydown", handleKeyDown)
    }, [subject, topic, parentTopic, litID, content, body, selectedProject])
  
    return (
      <div style={{ display: "flex", flexDirection: "column", padding: "1rem", height: "100%" }}>
        {/* Projektleiste */}
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
        <select value={selectedProject} onChange={(e) => {
        setSelectedProject(e.target.value)
        loadSourceByProject(e.target.value)
        }}>
        <option value="">-- auswählen --</option>
        {projects.map(p => (
            <option key={p} value={p}>{p}</option>  // ✅ Übergibt den ganzen Pfad wie "RG_Test25/RG_Test25.tex"
        ))}
        </select>
          <button onClick={() => loadSourceByProject(selectedProject)} style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem" }}>🔄</button>
          <button onClick={saveSource} style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem" }}>💾</button>
          <button onClick={handleSubmit} style={{ fontSize: "0.7rem", padding: "0.2rem 0.6rem", backgroundColor: "#3c3", color: "black" }}>Snip</button>
        </div>
  
        {/* Eingabemaske */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "0.3rem", fontSize: "0.75rem", marginBottom: "0.5rem" }}>
          <div><label>LitID:<input type="checkbox" checked={freezeLitID} onChange={() => setFreezeLitID(f => !f)} style={{ marginLeft: "0.4rem" }} /></label><input value={litID} onChange={e => setLitID(e.target.value)} style={{ width: "100%" }} /></div>
          <div><label>Subject:<input type="checkbox" checked={freezeSubject} onChange={() => setFreezeSubject(f => !f)} style={{ marginLeft: "0.4rem" }} /></label><input list="subjects" value={subject} onChange={e => { setSubject(e.target.value); if (!topicMap[e.target.value]?.topics?.[topic]) { setTopic(""); setParentTopic(""); } }} style={{ width: "100%" }} /><datalist id="subjects">{Object.keys(topicMap).map(s => <option key={s} value={s} />)}</datalist></div>
          <div><label>Topic:<input type="checkbox" checked={freezeTopic} onChange={() => setFreezeTopic(f => !f)} style={{ marginLeft: "0.4rem" }} /></label><input list="topics" value={topic} onChange={e => { setTopic(e.target.value); const pt = topicMap[subject]?.topics?.[e.target.value]?.parent; if (pt) setParentTopic(pt) }} style={{ width: "100%" }} /><datalist id="topics">{(topicMap[subject]?.topics ? Object.keys(topicMap[subject].topics) : []).map(t => <option key={t} value={t} />)}</datalist></div>
          <div><label>ParentTopic:<input type="checkbox" checked={freezeParent} onChange={() => setFreezeParent(f => !f)} style={{ marginLeft: "0.4rem" }} /></label><input list="parents" value={parentTopic} onChange={e => setParentTopic(e.target.value)} style={{ width: "100%" }} /><datalist id="parents">{Array.from(new Set(Object.values(topicMap[subject]?.topics || {}).map(t => t.parent).filter(Boolean))).map(p => (<option key={p} value={p} />))}</datalist></div>
          <div><label>Content:</label><input value={content} onChange={e => setContent(e.target.value)} style={{ width: "100%" }} /></div>
          <div><label>CTyp:</label><select value={ctyp} onChange={e => setCtyp(e.target.value)} style={{ width: "100%" }}>{["DEF", "EXA", "PROP", "REM", "THEO"].map(k => <option key={k} value={k}>{k}</option>)}</select></div>
        </div>
   
        {/* ACE Editor */}
        <div style={{ flex: 1 }}>
          <AceEditor
            ref={aceRef}
            mode="latex_custom"
            theme="twilight"
            value={body}
            onChange={setBody}
            name="editor"
            width="100%"
            height="100%"
            fontSize={12}
            setOptions={{ useWorker: false, wrap: true }}
          />
        </div>
      </div>
    )
  })
  
  export default TexSnipEditor
  