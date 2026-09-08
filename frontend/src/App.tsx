import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Camera, ChevronRight, CircleDot, MapPinned, RefreshCw, Route, ShieldCheck } from 'lucide-react'
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
  const activeAlerts = alerts.filter(a=>!a.acknowledged).length
  return <main>
    <header className="topbar"><div className="brand"><div className="brand-mark"><ShieldCheck size={19}/></div><div><b>SENTINEL COMMAND</b><span>OPERATIONS CONSOLE · GUJARAT</span></div></div><div className="system-state"><span className={`state-dot ${mode === 'live' ? 'is-live' : 'is-demo'}`}/><div><strong>{mode === 'live' ? 'LIVE MODE' : 'DEMONSTRATION MODE'}</strong><small>Last refresh {new Date().toLocaleTimeString()}</small></div></div><button onClick={sync} className="sync"><RefreshCw size={15}/> Refresh catalogue</button></header>
    {error && <div className="error"><AlertTriangle size={16}/>{error}</div>}
    <section className="page-heading"><div><p className="section-kicker">CONTROL ROOM / OVERVIEW</p><h1>Operational overview</h1><p className="sub">Camera availability, detections, and priority alerts across the monitored area.</p></div><div className="heading-meta"><span>REGION</span><b>Ahmedabad District</b><span>DATA SOURCE</span><b>{mode === 'live' ? 'Sentinel gateway' : 'Local demonstration data'}</b></div></section>
    <section className="summary-grid"><Metric label="CAMERAS ONLINE" value={String(cameras.length).padStart(2,'0')} icon={<Camera/>}/><Metric label="UNACKNOWLEDGED ALERTS" value={String(activeAlerts).padStart(2,'0')} icon={<AlertTriangle/>}/><Metric label="DETECTION EVENTS" value={String(events.length).padStart(2,'0')} icon={<CircleDot/>}/><Metric label="SYSTEM STATUS" value="OK" icon={<ShieldCheck/>}/></section>
    <section className="workspace"><div className="panel map-card"><div className="card-title"><div><MapPinned size={16}/><b>Camera coverage</b><span>Geographic view</span></div><span className="panel-tag">{cameras.length} REGISTERED</span></div><OperationalMap cameras={cameras} route={routeEvents} selectedId={selected?.id} onSelect={selectCamera} mapKey={mapKey}/></div>
      <aside className="panel side-panel"><div className="card-title"><div><AlertTriangle size={16}/><b>Priority alerts</b></div><span className="count-badge">{activeAlerts}</span></div>{alerts.length===0?<p className="empty">No priority alerts.</p>:alerts.map(a=><article className="alert" key={a.id}><span className={`severity ${a.severity}`}/><div><b>{a.title}</b><p>{a.description}</p><small>{a.camera_id} · {new Date(a.created_at).toLocaleTimeString()}</small></div><ChevronRight size={15}/></article>)}</aside></section>
    <section className="lower"><div className="panel feed"><div className="card-title"><div><Camera size={16}/><b>Camera inspection</b></div><span className={`status-label ${selected?.status === 'live' ? 'live' : ''}`}>{selected?.status||'NO SELECTION'}</span></div>{selected?<><VideoPreview hlsUrl={selected.streams.hls} whepUrl={selected.streams.whep}/><div className="camera-detail"><div><h3>{selected.name}</h3><p className="muted">{selected.id} · {selected.codec||'Codec pending'} · {selected.width||'—'}×{selected.height||'—'}</p></div><button className="outline-button" onClick={()=>setSelected(selected)}>Selected camera</button></div></>:<p className="empty">Select a camera from the map.</p>}</div>
      <div className="panel timeline"><div className="card-title"><div><Route size={16}/><b>Recent detection events</b></div><span className="panel-tag">LAST 5</span></div>{events.slice(0,5).map(e=><article className="event" key={e.id}><time>{new Date(e.occurred_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</time><i/><div><b>{e.plate||e.entity_id}</b><p>{e.camera_id} · confidence {Math.round(e.confidence*100)}%</p></div></article>)}</div>
      <div className="panel principles"><div className="card-title"><div><ShieldCheck size={16}/><b>System controls</b></div></div><div className="control-row"><span>Catalogue sync</span><strong>ENABLED</strong></div><div className="control-row"><span>RTSP transport</span><strong>TCP</strong></div><div className="control-row"><span>Source timing</span><strong>PTS</strong></div><div className="control-row"><span>Reconnect policy</span><strong>BACKOFF</strong></div></div></section>
  </main>
}
function Metric({label,value,icon}:{label:string;value:string;icon:ReactNode}) { return <div className="metric"><div>{icon}</div><b>{value}</b><span>{label}</span></div> }
export default App