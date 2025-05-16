// src/hooks/useUnits.js
import { useEffect, useState } from 'react';

export function useUnits() {
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/units')
      .then(res => res.json())
      .then(data => {
        setUnits(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Fehler beim Abrufen der Units:', err);
        setLoading(false);
      });
  }, []);

  return { units, loading };
}
