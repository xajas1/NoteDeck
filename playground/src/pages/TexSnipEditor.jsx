// playground/src/pages/TexSnipEditor.jsx
import React, { useEffect, useState, useRef } from "react";
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-latex";
import "ace-builds/src-noconflict/theme-twilight";

export default function TexSnipEditor() {
  const [subject, setSubject] = useState("A");
  const [topic, setTopic] = useState("Ringe Basics");
  const [litID, setLitID] = useState("T12");
  const [ctyp, setCtyp] = useState("DEF");
  const [parentTopic, setParentTopic] = useState("Ringe");
  const [content, setContent] = useState("");
  const [body, setBody] = useState("");

  const [freezeSubject, setFreezeSubject] = useState(true);
  const [freezeTopic, setFreezeTopic] = useState(true);
  const [freezeParent, setFreezeParent] = useState(true);
  const [freezeLitID, setFreezeLitID] = useState(true);

  const [topicMap, setTopicMap] = useState({});
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState("");

  const [response, setResponse] = useState(null);
  const aceRef = useRef(null);

  useEffect(() => {
    fetch("http://localhost:8000/topic-map")
      .then(res => res.json())
      .then(setTopicMap)
      .catch(err => console.error("Fehler beim Laden von /topic-map", err));

    fetch("http://localhost:8000/available-sources")
      .then(res => res.json())
      .then(setProjects)
      .catch(err => console.error("Fehler beim Laden der Projekte:", err));
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      const isCmd = e.metaKey || e.ctrlKey;
      const isEnter = e.key === "Enter";

      if (isCmd && isEnter && !e.shiftKey) {
        e.preventDefault();
        handleSaveSource();
      } else if (isCmd && isEnter && e.shiftKey) {
        e.preventDefault();
        handleLoadSource();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedProject, body]);

  const topicExists = () =>
    topicMap[subject] && Object.keys(topicMap[subject].topics || {}).includes(topic);

  const ensureTopicExists = async () => {
    if (!topicExists()) {
      const addPayload = { Subject: subject, Topic: topic, ParentTopic: parentTopic || null };
      const res = await fetch("http://localhost:8000/add-topic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(addPayload),
      });
      const json = await res.json();
      setTopicMap(prev => {
        const updated = { ...prev };
        if (!updated[subject]) updated[subject] = { index: 99, topics: {} };
        updated[subject].topics[topic] = { index: json.index, parent: parentTopic || null };
        return updated;
      });
    }
  };

  const handleTopicChange = (e) => {
    const newTopic = e.target.value;
    setTopic(newTopic);
    if (topicMap[subject] && topicMap[subject].topics[newTopic]) {
      const knownParent = topicMap[subject].topics[newTopic].parent;
      if (knownParent) setParentTopic(knownParent);
    }
  };

  const handleSubmit = async () => {
    await ensureTopicExists();
    const editor = aceRef.current?.editor;
    if (!editor) return;

    const selectedText = editor.getSelectedText().trim();
    if (!selectedText) {
      setResponse({ status: "error", message: "Kein Bereich markiert." });
      return;
    }

    const payload = {
      Subject: subject,
      Topic: topic,
      LitID: litID,
      CTyp: ctyp,
      Content: content,
      Body: selectedText,
      ParentTopic: parentTopic,
      project: selectedProject,
    };

    try {
      const res = await fetch("http://localhost:8000/snip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const json = await res.json();
      setResponse(json);

      if (json.UnitID) {
        const wrappedText = `\\begin{${ctyp}}{${json.UnitID}}{${content}}\n${selectedText}\n\\end{${ctyp}}`;
        const range = editor.getSelectionRange();
        editor.session.replace(range, wrappedText);
        setBody(editor.getValue());
      }

      if (!freezeSubject) setSubject("");
      if (!freezeTopic) setTopic("");
      if (!freezeParent) setParentTopic("");
      if (!freezeLitID) setLitID("");

    } catch (error) {
      setResponse({ status: "error", message: error.message });
    }
  };

  const handleProjectChange = async (e) => {
    const newProject = e.target.value;
    setSelectedProject(newProject);
    await loadSourceByProject(newProject);
  };

  const loadSourceByProject = async (projectName) => {
    if (!projectName) return;
    try {
      const res = await fetch(`http://localhost:8000/load-source?project=${projectName}`);
      const json = await res.json();
      setBody(json.content || "");
    } catch (err) {
      console.error("Fehler beim Laden der Datei:", err);
    }
  };

  const handleLoadSource = () => {
    if (selectedProject) loadSourceByProject(selectedProject);
  };

  const handleSaveSource = async () => {
    if (!selectedProject) return;
    try {
      const res = await fetch("http://localhost:8000/save-source", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project: selectedProject, content: body }),
      });
      const json = await res.json();
      console.log("Speichern:", json);
    } catch (err) {
      console.error("Fehler beim Speichern:", err);
    }
  };

  return (
    <div style={{ width: "100vw", height: "100vh", display: "flex", flexDirection: "row", fontFamily: "sans-serif", backgroundColor: "#1e1e1e", color: "#f0f0f0", overflow: "hidden" }}>
      <div style={{ flex: 3, display: "flex", flexDirection: "column", padding: "0.5rem", overflow: "hidden" }}>
        <h4 style={{ margin: "0 0 0.3rem 0", fontSize: "1.1rem" }}>📄 Tex Snip Editor</h4>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", marginBottom: "0.3rem" }}>
          <label>Projekt:</label>
          <select value={selectedProject} onChange={handleProjectChange} style={{ flex: 1 }}>
            <option value="">-- auswählen --</option>
            {projects.map((p) => (
              <option key={p} value={p.split("/")[0]}>{p}</option>
            ))}
          </select>
          <button onClick={handleLoadSource} style={{ padding: "0.25rem 0.5rem", fontSize: "0.8rem" }}>🔄 Laden</button>
          <button onClick={handleSaveSource} style={{ padding: "0.25rem 0.5rem", fontSize: "0.8rem" }}>💾 Speichern</button>
          <button onClick={handleSubmit} style={{ padding: "0.25rem 0.5rem", backgroundColor: "#2c2", color: "black", fontSize: "0.8rem" }}>✅ Snip</button>
          {response && (
            <div style={{ fontSize: "0.8rem", marginLeft: "auto" }}>
              <strong>Status:</strong> {response.status}
              {response.UnitID && <span style={{ marginLeft: "0.5rem" }}><strong>UnitID:</strong> {response.UnitID}</span>}
            </div>
          )}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "0.3rem", marginBottom: "0.3rem" }}>
          <div>
            <label style={{ fontSize: "0.8rem" }}>Subject:
              <input type="checkbox" checked={freezeSubject} onChange={() => setFreezeSubject(f => !f)} style={{ marginLeft: "0.5rem" }} />
            </label>
            <input style={{ width: "100%" }} list="subjects" value={subject} onChange={(e) => setSubject(e.target.value)} />
          </div>
          <div>
            <label style={{ fontSize: "0.8rem" }}>Topic:
              <input type="checkbox" checked={freezeTopic} onChange={() => setFreezeTopic(f => !f)} style={{ marginLeft: "0.5rem" }} />
            </label>
            <input style={{ width: "100%" }} list="topics" value={topic} onChange={handleTopicChange} />
          </div>
          <div>
            <label style={{ fontSize: "0.8rem" }}>ParentTopic:
              <input type="checkbox" checked={freezeParent} onChange={() => setFreezeParent(f => !f)} style={{ marginLeft: "0.5rem" }} />
            </label>
            <input style={{ width: "100%" }} list="parents" value={parentTopic} onChange={(e) => setParentTopic(e.target.value)} />
          </div>
          <div>
            <label style={{ fontSize: "0.8rem" }}>LitID:
              <input type="checkbox" checked={freezeLitID} onChange={() => setFreezeLitID(f => !f)} style={{ marginLeft: "0.5rem" }} />
            </label>
            <input style={{ width: "100%" }} value={litID} onChange={(e) => setLitID(e.target.value)} />
          </div>
          <div>
            <label style={{ fontSize: "0.8rem" }}>CTyp:</label>
            <select style={{ width: "100%" }} value={ctyp} onChange={(e) => setCtyp(e.target.value)}>
              <option value="DEF">DEF</option>
              <option value="EXA">EXA</option>
              <option value="PROP">PROP</option>
              <option value="REM">REM</option>
              <option value="THEO">THEO</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: "0.8rem" }}>Content:</label>
            <input style={{ width: "100%" }} value={content} onChange={(e) => setContent(e.target.value)} />
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", border: "1px solid #444" }}>
          <AceEditor
            ref={aceRef}
            mode="latex"
            theme="twilight"
            value={body}
            onChange={setBody}
            name="tex-editor"
            width="100%"
            height="100%"
            fontSize={14}
            setOptions={{ useWorker: false, wrap: true }}
          />
        </div>
      </div>

      <div style={{ flex: 2, padding: "1rem", borderLeft: "1px solid #444", backgroundColor: "#2a2a2a", overflowY: "auto" }}>
        <h3>🔍 Vorschau & Struktur</h3>
        <p style={{ fontSize: "0.9rem", color: "#aaa" }}>Hier kannst du später die ENV-Vorschau und die Topic-Tree-Struktur sehen.</p>
      </div>
    </div>
  );
}
