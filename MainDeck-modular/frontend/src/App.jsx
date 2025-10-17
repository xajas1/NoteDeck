// src/App.jsx
import { useUnits } from './hooks/useUnits';
import { UnitList } from './components/UnitList';

function App() {
  const { units, loading } = useUnits();

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
      <h1>📚 NoteDeck Playground</h1>
      {loading ? <p>Lade Einheiten …</p> : <UnitList units={units} />}
    </div>
  );
}

export default App;
