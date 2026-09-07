import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { GeoJSONSource, Map, Marker, StyleSpecification } from 'maplibre-gl'
import type { Feature, LineString } from 'geojson'
import 'maplibre-gl/dist/maplibre-gl.css'

type Point = { latitude: number; longitude: number }
type CameraItem = { id: string; name: string; location: Point; status: string; streams: { rtsp?: string; hls?: string; whep?: string } }
type EventItem = { id: string; location: Point }

const fallbackStyle: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
}

export function OperationalMap({
  cameras,
  route,
  selectedId,
  onSelect,
  mapKey,
}: {
  cameras: CameraItem[]
  route: EventItem[]
  selectedId?: string
  onSelect: (camera: CameraItem) => void
  mapKey: string
}) {
  const mapNode = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const markers = useRef<Marker[]>([])

  useEffect(() => {
    if (!mapNode.current || mapRef.current) return
    const style = mapKey
      ? `https://api.maptiler.com/maps/streets-v2/style.json?key=${encodeURIComponent(mapKey)}`
      : fallbackStyle
    mapRef.current = new maplibregl.Map({
      container: mapNode.current,
      style,
      center: [72.55, 23.03],
      zoom: 11.3,
    })
    mapRef.current.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      'top-right'
    )
    return () => {
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [mapKey])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const render = () => {
      markers.current.forEach((marker: Marker) => marker.remove())
      markers.current = []
      cameras.forEach((camera) => {
        const element = document.createElement('button')
        element.className = `map-camera ${camera.id === selectedId ? 'is-selected' : ''}`
        element.type = 'button'
        element.setAttribute('aria-label', `Open ${camera.name}`)
        element.textContent = '●'
        element.onclick = () => onSelect(camera)
        markers.current.push(
          new maplibregl.Marker({ element })
            .setLngLat([camera.location.longitude, camera.location.latitude])
            .addTo(map)
        )
      })
      const coordinates = route.map((event) => [
        event.location.longitude,
        event.location.latitude,
      ])
      const source = map.getSource('route') as GeoJSONSource | undefined
      const data: Feature<LineString> = {
        type: 'Feature',
        properties: {},
        geometry: { type: 'LineString', coordinates },
      }
      if (source) {
        source.setData(data)
      } else {
        map.addSource('route', { type: 'geojson', data })
        map.addLayer({
          id: 'route',
          type: 'line',
          source: 'route',
          paint: {
            'line-color': '#e4ae35',
            'line-width': 4,
            'line-dasharray': [1.4, 1],
          },
        })
      }
    }
    if (map.isStyleLoaded()) render()
    else map.once('load', render)
  }, [cameras, route, selectedId, onSelect])

  return <div ref={mapNode} className="real-map" aria-label="Operational camera map" />
}
