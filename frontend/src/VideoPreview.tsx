import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'

export function VideoPreview({ hlsUrl, whepUrl }: { hlsUrl?: string; whepUrl?: string }) {
  const video = useRef<HTMLVideoElement>(null)
  const [message, setMessage] = useState('Waiting for catalogue stream URL')
  useEffect(() => {
    const node = video.current
    if (!node || !hlsUrl) return
    if (node.canPlayType('application/vnd.apple.mpegurl')) { node.src = hlsUrl; setMessage('Live HLS preview ready'); return }
    if (!Hls.isSupported()) { setMessage('This browser cannot play HLS; use the WebRTC/WHEP operator preview.'); return }
    const hls = new Hls({ lowLatencyMode: true, enableWorker: true })
    hls.loadSource(hlsUrl); hls.attachMedia(node)
    hls.on(Hls.Events.MANIFEST_PARSED, () => setMessage('Live HLS preview ready'))
    hls.on(Hls.Events.ERROR, (_, data) => { if (data.fatal) setMessage('Preview temporarily unavailable; stream worker remains independent.') })
    return () => hls.destroy()
  }, [hlsUrl])
  return <div className="video">{hlsUrl && <video ref={video} controls muted playsInline/>}<div className="video-message"><p>{hlsUrl ? 'ON-DEMAND HLS PREVIEW' : 'ON-DEMAND PREVIEW'}</p><span>{hlsUrl ? message : whepUrl ? 'WHEP preview URL available. Select WebRTC mode in production deployment.' : message}</span></div></div>
}

