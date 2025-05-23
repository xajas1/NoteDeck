import React from 'react'
import Split from '@uiw/react-split'
import TexSnipEditor from './TexSnipEditor'
import TexSnipTablePage from './TexSnipTablePage'

const TexSplitViewPage = () => {
  return (
    <div style={{ height: '100vh', width: '100vw' }}>
      <Split mode="horizontal" min={200} style={{ height: '100%' }}>
        <div style={{ padding: 0, overflow: 'auto' }}>
          <TexSnipEditor />
        </div>
        <div style={{ padding: 0, overflow: 'auto' }}>
          <TexSnipTablePage />
        </div>
      </Split>
    </div>
  )
}

export default TexSplitViewPage
