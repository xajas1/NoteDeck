import { useState, useMemo } from 'react'

export default function TreeSidebar({ units, playground, setPlayground }) {
  const [expandedPaths, setExpandedPaths] = useState(new Set())

  const isSelected = (uid) => playground.some(p => p.UnitID === uid)

  const toggleUnit = (unit) => {
    if (isSelected(unit.UnitID)) {
      setPlayground(playground.filter(u => u.UnitID !== unit.UnitID))
    } else {
      setPlayground([...playground, {
        UnitID: unit.UnitID,
        Name: unit.Content,
        Section: "",
        Subsection: "",
        Order: playground.length + 1
      }])
    }
  }

  const toggleExpand = (path) => {
    const next = new Set(expandedPaths)
    next.has(path) ? next.delete(path) : next.add(path)
    setExpandedPaths(next)
  }

  const buildTree = (units) => {
    const tree = {}

    for (const u of units) {
      const subject = u.Subject
      const source = u.LitID || '⟨Ohne Quelle⟩'
      const pathParts = [...u.TopicPath.split('/'), source]

      let node = tree[subject] ??= {}

      for (const part of pathParts) {
        node.children ??= {}
        node = node.children[part] ??= {}
      }

      node.units ??= []
      node.units.push(u)
    }

    return tree
  }

  const treeData = useMemo(() => buildTree(units), [units])

  const collectAllUnitIDs = (node) => {
    let ids = [...(node.units || []).map(u => u.UnitID)]
    for (const child of Object.values(node.children || {})) {
      ids.push(...collectAllUnitIDs(child))
    }
    return ids
  }

  const isNodeChecked = (node) =>
    collectAllUnitIDs(node).every(id => playground.some(p => p.UnitID === id))

  const toggleNodeUnits = (node) => {
    const ids = collectAllUnitIDs(node)
    const currentIDs = new Set(playground.map(p => p.UnitID))
    const allSelected = ids.every(id => currentIDs.has(id))

    const newPlayground = allSelected
      ? playground.filter(p => !ids.includes(p.UnitID))
      : [...playground, ...units.filter(u => ids.includes(u.UnitID) && !currentIDs.has(u.UnitID))]

    setPlayground(newPlayground)
  }

  const renderNode = (node, fullPath = '', level = 1) => {
    const entries = Object.entries(node.children || {})
    const indent = { paddingLeft: `${level * 0.3}rem` }

    return (
      <div>
        {entries.map(([name, child]) => {
          const thisPath = fullPath ? `${fullPath}/${name}` : name
          const isOpen = expandedPaths.has(thisPath)

          return (
            <div key={thisPath} style={indent}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <span
                  onClick={() => toggleExpand(thisPath)}
                  style={{ cursor: 'pointer', marginRight: '0.0rem' }}
                >
                  {isOpen ? '▼' : '▶'}
                </span>
                <input
                  type="checkbox"
                  checked={isNodeChecked(child)}
                  onChange={() => toggleNodeUnits(child)}
                  style={{ marginRight: '0.4rem' }}
                />
                <span
                  style={{ fontWeight: 'bold', cursor: 'pointer' }}
                  onClick={() => toggleExpand(thisPath)}
                >
                  {name}
                </span>
              </div>
              {isOpen && (
                <div>
                  {child.units?.map(unit => (
                    <label key={unit.UnitID} style={{ display: 'block', marginLeft: '1.6rem' }}>
                      <input
                        type="checkbox"
                        checked={isSelected(unit.UnitID)}
                        onChange={() => toggleUnit(unit)}
                        style={{ marginRight: '0.5rem' }}
                      />
                      <span style={{ fontSize: '0.85rem' }}>{unit.UnitID}: {unit.Content}</span>
                    </label>
                  ))}
                  {renderNode(child, thisPath, level + 1)}
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div style={{ color: '#eee', fontSize: '0.9rem' }}>
      <h3 style={{ fontWeight: 'bold', marginBottom: '1rem' }}>📚 Inhalte</h3>
      {Object.entries(treeData).map(([subject, tree]) => (
        <div key={subject} style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span
              onClick={() => toggleExpand(subject)}
              style={{ cursor: 'pointer', marginRight: '0.3rem' }}
            >
              {expandedPaths.has(subject) ? '▼' : '▶'}
            </span>
            <input
              type="checkbox"
              checked={isNodeChecked(tree)}
              onChange={() => toggleNodeUnits(tree)}
              style={{ marginRight: '0.4rem' }}
            />
            <span
              style={{ fontWeight: 'bold', cursor: 'pointer' }}
              onClick={() => toggleExpand(subject)}
            >
              {subject}
            </span>
          </div>
          {expandedPaths.has(subject) && (
            <div style={{ marginLeft: '1rem' }}>
              {renderNode(tree, subject, 1)}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
