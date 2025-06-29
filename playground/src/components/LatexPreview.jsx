import React, { useMemo } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const LatexPreview = ({ code = '' }) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(code, {
        throwOnError: false,
        displayMode: true
      })
    } catch (err) {
      return `<pre>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>`
    }
  }, [code])

  return (
    <div
      style={{ padding: '1rem', overflow: 'auto', height: '100%', background: '#fff', color: '#000' }}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

export default LatexPreview
