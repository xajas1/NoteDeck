import { useState } from 'react'
import {
  useSortable,
  SortableContext,
  verticalListSortingStrategy
} from '@dnd-kit/sortable'
import { useDroppable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'

export default function TreeEditorView({
  structure,
  setStructure,
  units,
  selectedEditorIDs,
  setSelectedEditorIDs,
  lastSelectedEditorIndex,
  setLastSelectedEditorIndex
}) {
  const [newSectionName, setNewSectionName] = useState('')
  const [subInputs, setSubInputs] = useState({})
  const [collapsedSections, setCollapsedSections] = useState(new Set())
  const [collapsedSubsections, setCollapsedSubsections] = useState(new Set())

  const toggleCollapseSection = (id) => {
    setCollapsedSections(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleCollapseSubsection = (id) => {
    setCollapsedSubsections(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const getUnitByID = (id) => units.find(u => u.UnitID === id)

  const toggleSelection = (fullID, index, shift = false, allIDs = []) => {
    setSelectedEditorIDs(prev => {
      const next = new Set(prev)
      if (shift && lastSelectedEditorIndex !== null) {
        const start = Math.min(lastSelectedEditorIndex, index)
        const end = Math.max(lastSelectedEditorIndex, index)
        for (let i = start; i <= end; i++) next.add(allIDs[i])
      } else {
        next.has(fullID) ? next.delete(fullID) : next.add(fullID)
        setLastSelectedEditorIndex(index)
      }
      return next
    })
  }

  const addSection = () => {
    if (!newSectionName.trim()) return
    setStructure([...structure, {
      id: `sec-${Date.now()}`,
      name: newSectionName,
      subsections: []
    }])
    setNewSectionName('')
  }

  return (
    <div style={{ fontFamily: 'monospace', fontSize: '0.78rem', color: '#eee' }}>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.7rem' }}>
        <input
          type="text"
          value={newSectionName}
          onChange={e => setNewSectionName(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') addSection() }}
          placeholder="Neue Section"
          style={{ backgroundColor: '#111', color: '#eee', padding: '0.2rem', fontSize: '0.75rem', flex: 1 }}
        />
        <button onClick={addSection} style={styles.button}>Add</button>
      </div>

      <SortableContext items={structure.map(s => s.id)} strategy={verticalListSortingStrategy}>
        {structure.map(section => (
          <SortableSection
            key={section.id}
            section={section}
            setStructure={setStructure}
            subInputs={subInputs}
            setSubInputs={setSubInputs}
            getUnitByID={getUnitByID}
            selectedEditorIDs={selectedEditorIDs}
            toggleSelection={toggleSelection}
            lastSelectedEditorIndex={lastSelectedEditorIndex}
            setLastSelectedEditorIndex={setLastSelectedEditorIndex}
            collapsedSections={collapsedSections}
            collapsedSubsections={collapsedSubsections}
            toggleCollapseSection={toggleCollapseSection}
            toggleCollapseSubsection={toggleCollapseSubsection}
          />
        ))}
      </SortableContext>
    </div>
  )
}

function SortableSection({
  section,
  setStructure,
  subInputs,
  setSubInputs,
  getUnitByID,
  selectedEditorIDs,
  toggleSelection,
  lastSelectedEditorIndex,
  setLastSelectedEditorIndex,
  collapsedSections,
  collapsedSubsections,
  toggleCollapseSection,
  toggleCollapseSubsection
}) {
  const {
    setNodeRef,
    transform,
    transition,
    attributes,
    listeners,
    isDragging
  } = useSortable({
    id: section.id,
    data: { type: 'section' }
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    marginBottom: '1.5rem'
  }

  const isCollapsed = collapsedSections.has(section.id)

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <div
        style={styles.section}
        onClick={() => toggleCollapseSection(section.id)}
      >
        <span style={{ cursor: 'pointer', marginRight: '0.4rem' }}>
          {isCollapsed ? '▶' : '▼'}
        </span>
        {section.name}
      </div>

      {!isCollapsed && (
        <>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.3rem', marginLeft: '1rem' }}>
            <input
              type="text"
              value={subInputs[section.id] || ''}
              onChange={e => setSubInputs({ ...subInputs, [section.id]: e.target.value })}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const name = subInputs[section.id] || ''
                  setSubInputs({ ...subInputs, [section.id]: '' })
                  setStructure(prev =>
                    prev.map(s =>
                      s.id === section.id
                        ? { ...s, subsections: [...s.subsections, { id: `sub-${Date.now()}`, name, unitIDs: [] }] }
                        : s
                    )
                  )
                }
              }}
              placeholder="Neue Subsection"
              style={{ backgroundColor: '#111', color: '#eee', padding: '0.2rem', fontSize: '0.72rem', flex: 1 }}
            />
            <button
              onClick={() => {
                const name = subInputs[section.id] || ''
                setSubInputs({ ...subInputs, [section.id]: '' })
                setStructure(prev =>
                  prev.map(s =>
                    s.id === section.id
                      ? { ...s, subsections: [...s.subsections, { id: `sub-${Date.now()}`, name, unitIDs: [] }] }
                      : s
                  )
                )
              }}
              style={styles.subButton}
            >
              Add
            </button>
          </div>

          <SortableContext items={section.subsections.map(sub => sub.id)} strategy={verticalListSortingStrategy}>
            {section.subsections.map(sub => (
              <SortableSubsection
                key={sub.id}
                subsection={sub}
                sectionId={section.id}
                getUnitByID={getUnitByID}
                selectedEditorIDs={selectedEditorIDs}
                toggleSelection={toggleSelection}
                lastSelectedEditorIndex={lastSelectedEditorIndex}
                setLastSelectedEditorIndex={setLastSelectedEditorIndex}
                setStructure={setStructure}
                isCollapsed={collapsedSubsections.has(sub.id)}
                toggleCollapse={() => toggleCollapseSubsection(sub.id)}
              />
            ))}
          </SortableContext>
        </>
      )}
    </div>
  )
}

function SortableSubsection({
  subsection,
  sectionId,
  getUnitByID,
  selectedEditorIDs,
  toggleSelection,
  lastSelectedEditorIndex,
  setLastSelectedEditorIndex,
  setStructure,
  isCollapsed,
  toggleCollapse
}) {
  const {
    setNodeRef,
    transform,
    transition,
    attributes,
    listeners,
    isDragging
  } = useSortable({
    id: subsection.id,
    data: { type: 'subsection', parentId: sectionId }
  })

  const allIDs = subsection.unitIDs.map(id => `${subsection.id}__${id}`)

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={{
        ...styles.subsection,
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1
      }}
    >
      <div
        style={styles.subsectionName}
        onClick={toggleCollapse}
      >
        <span style={{ cursor: 'pointer', marginRight: '0.4rem' }}>
          {isCollapsed ? '▶' : '▼'}
        </span>
        {subsection.name}
      </div>

      {!isCollapsed && (
        <SortableContext items={allIDs} strategy={verticalListSortingStrategy}>
          <ul style={styles.ul}>
            {subsection.unitIDs.map((uid, index) => {
              const fullID = `${subsection.id}__${uid}`
              const unit = getUnitByID(uid)
              return (
                <SortableUnit
                  key={fullID}
                  id={fullID}
                  uid={uid}
                  fullID={fullID}
                  index={index}
                  ctyp={unit?.CTyp}
                  name={unit?.Content}
                  isSelected={selectedEditorIDs.has(fullID)}
                  selectedEditorIDs={selectedEditorIDs}
                  toggleSelection={toggleSelection}
                  lastSelectedEditorIndex={lastSelectedEditorIndex}
                  setLastSelectedEditorIndex={setLastSelectedEditorIndex}
                  allIDs={allIDs}
                  setStructure={setStructure}
                />
              )
            })}
          </ul>
        </SortableContext>
      )}
    </div>
  )
}

function SortableUnit({
  id,
  uid,
  fullID,
  index,
  ctyp,
  name,
  isSelected,
  selectedEditorIDs,
  toggleSelection,
  lastSelectedEditorIndex,
  setLastSelectedEditorIndex,
  allIDs,
  setStructure
}) {
  const {
    setNodeRef,
    attributes,
    listeners,
    transform,
    transition,
    isDragging
  } = useSortable({
    id,
    data: {
      type: 'unit',
      draggedIDs:
        isSelected && selectedEditorIDs.size > 1
          ? Array.from(selectedEditorIDs).map(x => x.split('__')[1])
          : [uid]
    }
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    padding: '0rem 0.2rem',
    backgroundColor: isSelected ? '#2a2a2a' : 'transparent',
    borderLeft: isSelected ? '2px solid #4fc3f7' : '2px solid transparent',
    fontSize: '0.68rem',
    lineHeight: '0.95rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.02rem',
    cursor: 'grab'
  }

  const handleRemove = (e) => {
    e.stopPropagation()
    setStructure(prev =>
      prev.map(section => ({
        ...section,
        subsections: section.subsections.map(sub =>
          sub.id === fullID.split('__')[0]
            ? { ...sub, unitIDs: sub.unitIDs.filter(id => id !== uid) }
            : sub
        )
      }))
    )
  }

  return (
    <li
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      onClick={(e) => {
        e.stopPropagation()
        toggleSelection(fullID, index, e.shiftKey, allIDs)
      }}
      style={style}
    >
      <span>
        <span style={{ fontWeight: 'bold', color: '#7dd3fc' }}>[{ctyp}]</span>{' '}
        <strong>{uid}</strong>: <span style={{ color: '#bbb' }}>{name}</span>
      </span>
      <button
        onClick={handleRemove}
        style={{
          background: 'transparent',
          color: '#60a5fa',
          border: 'none',
          cursor: 'pointer',
          marginLeft: '0.4rem',
          fontSize: '0.72rem',
          lineHeight: '1rem'
        }}
      >
        ✕
      </button>
    </li>
  )
}

const styles = {
  button: {
    backgroundColor: '#333',
    color: '#eee',
    padding: '0.2rem 0.5rem',
    borderRadius: '4px',
    border: 'none',
    fontSize: '0.75rem',
    cursor: 'pointer'
  },
  subButton: {
    backgroundColor: '#222',
    color: '#ccc',
    padding: '0.2rem 0.4rem',
    borderRadius: '3px',
    border: 'none',
    fontSize: '0.72rem',
    cursor: 'pointer'
  },
  section: {
    fontWeight: 'bold',
    marginTop: '1.2rem',
    marginBottom: '0.4rem',
    fontSize: '0.9rem',
    display: 'flex',
    alignItems: 'center',
    cursor: 'pointer'
  },
  subsection: {
    marginLeft: '1rem',
    padding: '0.4rem',
    border: '1px dashed #666',
    borderRadius: '4px',
    backgroundColor: '#1e1e1e',
    marginTop: '0.6rem'
  },
  subsectionName: {
    fontWeight: 'bold',
    marginBottom: '0.2rem',
    fontSize: '0.8rem',
    cursor: 'pointer'
  },
  ul: {
    listStyle: 'none',
    paddingLeft: '0.6rem',
    margin: 0
  }
}
