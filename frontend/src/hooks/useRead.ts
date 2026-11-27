import {useCallback, useEffect, useState} from 'react';
import {read} from '../services/bridge';
import type {ReadResults} from '../types/bridge';

export function useRead<K extends keyof ReadResults>(section: K, revision: number = 0) {
  const [data, setData] = useState<ReadResults[K] | null>(null), [error, setError] = useState('');
  const refresh = useCallback(async () => {try {setData(await read(section)); setError('');} catch (e) {setError((e as Error).message);}}, [section]);
  useEffect(() => {let live = true; read(section).then(d => {if (live) {setData(d); setError('');}}).catch(e => {if (live) setError(e.message);}); return () => {live = false;};}, [section, revision]);
  return {data, error, refresh, setData};
}
