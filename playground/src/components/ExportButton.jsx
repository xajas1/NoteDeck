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
        const res = await fetch(`http://127.0.0.1:8000/export-project/${projectName}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(body)
        })
  
        const result = await res.json()
        alert(result.message || "Export abgeschlossen.")
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
  