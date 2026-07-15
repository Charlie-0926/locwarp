import { request, type SpeedOpts } from '../../../services/api'

export const startSpiralRequest = (
  center: { lat: number; lng: number },
  radiusM: number,
  spacingM: number,
  mode: string,
  speed?: SpeedOpts,
  udid?: string,
  straightLine?: boolean,
  routeEngine?: string,
) => request<any>('POST', '/api/location/spiral', {
  center,
  radius_m: radiusM,
  spacing_m: spacingM,
  mode,
  speed_kmh: speed?.speed_kmh ?? null,
  speed_min_kmh: speed?.speed_min_kmh ?? null,
  speed_max_kmh: speed?.speed_max_kmh ?? null,
  ...(straightLine ? { straight_line: true } : {}),
  ...(routeEngine ? { route_engine: routeEngine } : {}),
  ...(udid ? { udid } : {}),
})
