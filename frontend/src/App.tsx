import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Camera, ChevronRight, MapPinned, Radio, RefreshCw, Route, ShieldCheck } from 'lucide-react'
import { VideoPreview } from './VideoPreview'
import { OperationalMap } from './OperationalMap'
import './styles.css'

type Point = { latitude: number; longitude: number }
type CameraItem = { id:string; name:string; location:Point; status:string; codec?:string; width?:number; height?:number; streams:{rtsp?:string;hls?:string;whep?:string} }
type EventItem = { id:string; camera_id:string; entity_id:string; plate?:string; occurred_at:string; confidence:number; location:Point }
type AlertItem = { id:string; severity:string; title:string; description:string; camera_id:string; entity_id:string; created_at:string; acknowledged:boolean }
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function get<T>(path:string):Promise<T> { const r=await fetch(`${API}${path}`); if(!r.ok) throw new Error(await r.text()); return r.json() }

function App() {
  const [cameras, setCameras] = useState<CameraItem[]>([])
  const [events, setEvents] = useState<EventItem[]>([])
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [mode, setMode] = useState('loading')
  const [mapKey, setMapKey] = useState('')
  const [selected, setSelected] = useState<CameraItem | null>(null)
  const [error, setError] = useState('')
  const reload = async () => { try { setError(''); const [c,e,a,conf] = await Promise.all([get<CameraItem[]>('/api/cameras'),get<EventItem[]>('/api/events'),get<AlertItem[]>('/api/alerts'),get<{mode:string;maptilerKey:string}>('/api/config/public')]); setCameras(c);setEvents(e);setAlerts(a);setMode(conf.mode);setMapKey(conf.maptilerKey);setSelected(s=>s||c[0]||null) } catch(err) {setError(err instanceof Error?err.message:'Unable to reach API')} }
  useEffect(()=>{reload(); const id=window.setInterval(reload,15000); return ()=>window.clearInterval(id)},[])
  const routeEvents = useMemo(()=>selected ? events.filter(e=>e.entity_id==='vehicle:GJ01RX4582') : [],[events,selected])
  const selectCamera = useCallback((camera:CameraItem) => setSelected(camera), [])
  const sync = async()=>{try{await fetch(`${API}/api/cameras/sync`,{method:'POST'});await reload()}catch(err){setError(err instanceof Error?err.message:'Sync failed')}}
  return <main>
    <header><div className="brand"><div className="brand-mark"><ShieldCheck size={24}/></div><div><b>SENTINEL</b><span>COMMAND · GUJARAT</span></div></div><div className="status"><span className="pulse"/> {mode === 'live' ? 'LIVE GATEWAY CONNECTED' : 'DEMO MODE · GATEWAY READY'}</div><button onClick={sync} className="sync"><RefreshCw size={16}/> Sync cameras</button></header>
    {error && <div className="error">{error}</div>}
    <section className="hero"><div><p className="eyebrow">UNIFIED VIDEO INTELLIGENCE</p><h1>See the route.<br/><em>Act on the signal.</em></h1><p className="sub">Edge-first detection, watchlist intelligence, and a live operational picture for Gujarat.</p></div><div className="hero-metrics"><Metric label="CONNECTED CAMERAS" value={String(cameras.length).padStart(2,'0')} icon={<Camera/>}/><Metric label="ACTIVE ALERTS" value={String(alerts.filter(a=>!a.acknowledged).length).padStart(2,'0')} icon={<AlertTriangle/>}/><Metric label="TRACKED ENTITIES" value="01" icon={<Route/>}/></div></section>
    <section className="workspace"><div className="map-card"><div className="card-title"><div><MapPinned size={18}/><b>Operational map</b><span>Ahmedabad district</span></div><span className="live"><Radio size={14}/> LIVE</span></div><OperationalMap cameras={cameras} route={routeEvents} selectedId={selected?.id} onSelect={selectCamera} mapKey={mapKey}/></div>
      <aside className="side-panel"><div className="card-title"><div><AlertTriangle size={18}/><b>Priority alerts</b></div><span>{alerts.length}</span></div>{alerts.length===0?<p className="empty">No active alerts</p>:alerts.map(a=><article className="alert" key={a.id}><span className={`severity ${a.severity}`}/><div><b>{a.title}</b><p>{a.description}</p><small>{a.camera_id} · {new Date(a.created_at).toLocaleTimeString()}</small></div><ChevronRight size={16}/></article>)}</aside></section>
    <section className="lower"><div className="feed card"><div className="card-title"><div><Camera size={18}/><b>Camera inspection</b></div><span>{selected?.status||'—'}</span></div>{selected?<><VideoPreview hlsUrl={selected.streams.hls} whepUrl={selected.streams.whep}/><h3>{selected.name}</h3><p className="muted">{selected.id} · {selected.codec||'Codec pending'} · {selected.width||'—'}×{selected.height||'—'}</p></>:<p className="empty">No camera selected</p>}</div>
      <div className="timeline card"><div className="card-title"><div><Route size={18}/><b>Movement history</b></div><span>GJ01RX4582</span></div>{events.slice(0,5).map(e=><article className="event" key={e.id}><time>{new Date(e.occurred_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</time><i/><div><b>{e.plate||e.entity_id}</b><p>{e.camera_id} · confidence {Math.round(e.confidence*100)}%</p></div></article>)}</div>
      <div className="principles card"><div className="card-title"><div><ShieldCheck size={18}/><b>System integrity</b></div></div><p><span>01</span> Dynamic camera catalogue</p><p><span>02</span> RTSP transport over TCP</p><p><span>03</span> PTS-based tracking timing</p><p><span>04</span> Backoff & mixed-codec resilience</p></div></section>
  </main>
}
function Metric({label,value,icon}:{label:string;value:string;icon:ReactNode}) { return <div className="metric"><div>{icon}</div><b>{value}</b><span>{label}</span></div> }
export default App