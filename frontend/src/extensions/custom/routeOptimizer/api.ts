import { request } from '../../../services/api'

export interface RouteOptimizationResult {
  waypoints: { lat: number; lng: number }[]
  total_distance_m: number
  total_duration_s: number
  used_estimate?: boolean
}

export const optimizeRoute = (
  waypoints: { lat: number; lng: number }[],
  profile = 'foot',
  keepFirst = true,
  engine = 'osrm',
  straightLine = false,
) => request<RouteOptimizationResult>('POST', '/api/geocode/route-optimize', {
  waypoints,
  profile,
  keep_first: keepFirst,
  engine,
  ...(straightLine ? { straight_line: true } : {}),
})
