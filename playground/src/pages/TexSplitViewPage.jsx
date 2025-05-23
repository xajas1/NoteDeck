// /Users/tim/NoteDeck/playground/src/pages/TexSplitViewPage.jsx

import React from 'react'
import SplitPane from 'react-split-pane'
import TexSnipEditor from './TexSnipEditor'
import TexSnipTablePage from './TexSnipTablePage'

const TexSplitViewPage = () => {
  return (
    <div style={{ height: '100vh', width: '100vw' }}>
      <SplitPane
        split="vertical"
        minSize={300}
        defaultSize="55%"
        style={{ position: 'relative' }}
      >
        <div style={{ height: '100%', overflow: 'auto' }}>
          <TexSnipEditor />
        </div>
        <div style={{ height: '100%', overflow: 'auto', padding: '1rem' }}>
          <TexSnipTablePage />
        </div>
      </SplitPane>
    </div>
  )
}

export default TexSplitViewPage
