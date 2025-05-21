export default function ExportButton({ projectName, structure }) {
  const handleExport = async () => {
    if (!projectName || structure.length === 0) {
      alert("⚠️ Kein Projektname oder leere Struktur.");
      return;
    }

    const body = {
      projectName: projectName,
      structure: structure
    }

    try {
      // 1. JSON speichern
      const res1 = await fetch(`http://127.0.0.1:8000/export-project/${projectName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      const result1 = await res1.json()
      if (result1.status !== 'ok') {
        alert(`❌ JSON-Export fehlgeschlagen: ${result1.message}`)
        return
      }

      // 2. .tex-Datei erzeugen
      const res2 = await fetch(`http://127.0.0.1:8000/export-tex/${projectName}`, {
        method: 'POST'
      })
      const result2 = await res2.json()
      if (result2.status !== 'success') {
        alert(`❌ TeX-Export fehlgeschlagen: ${result2.message}`)
        return
      }

      alert(`✅ Export abgeschlossen: ${result2.message}`)
    } catch (err) {
      console.error("Export-Fehler:", err)
      alert("❌ Fehler beim Export.")
    }
  }

  return (
    <button onClick={handleExport} style={{
      backgroundColor: '#4a4',
      color: 'white',
      padding: '0.4rem 0.8rem',
      fontSize: '0.8rem',
      border: 'none',
      borderRadius: '5px',
      marginLeft: '1rem',
      cursor: 'pointer'
    }}>
      📤 TeX-Export
    </button>
  )
}
