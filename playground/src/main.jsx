import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

import './index.css'
import App from './App.jsx'
import TexSnipEditor from './pages/TexSnipEditor.jsx'
import TexSnipTablePage from './pages/TexSnipTablePage.jsx'
import TexSplitViewPage from './pages/TexSplitViewPage.jsx' // ✅ NEU

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/snip-editor" element={<TexSnipEditor />} />
        <Route path="/unit-table" element={<TexSnipTablePage />} />
        <Route path="/split-view" element={<TexSplitViewPage />} /> {/* ✅ NEU */}
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
