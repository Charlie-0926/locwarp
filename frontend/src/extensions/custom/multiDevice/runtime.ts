export interface RuntimePoint {
  lat: number
  lng: number
}

export interface DeviceRuntime {
  udid: string
  state: string
  currentPos: RuntimePoint | null
  destination: RuntimePoint | null
  routePath: RuntimePoint[]
  progress: number
  eta: number
  distanceRemaining: number
  distanceTraveled: number
  waypointIndex: number | null
  currentSpeedKmh: number
  error: string | null
  lapCount: number
  cooldown: number
}

export type RuntimesMap = Record<string, DeviceRuntime>

export interface FanoutOutcome<T> {
  ok: Array<{ udid: string; value: T }>
  failed: Array<{ udid: string; reason: string }>
}

export const emptyRuntime = (udid: string): DeviceRuntime => ({
  udid,
  state: 'idle',
  currentPos: null,
  destination: null,
  routePath: [],
  progress: 0,
  eta: 0,
  distanceRemaining: 0,
  distanceTraveled: 0,
  waypointIndex: null,
  currentSpeedKmh: 0,
  error: null,
  lapCount: 0,
  cooldown: 0,
})

export function summarizeResults<T>(
  results: PromiseSettledResult<T>[],
  udids: string[],
): FanoutOutcome<T> {
  const ok: FanoutOutcome<T>['ok'] = []
  const failed: FanoutOutcome<T>['failed'] = []
  results.forEach((result, index) => {
    const udid = udids[index]
    if (result.status === 'fulfilled') ok.push({ udid, value: result.value })
    else failed.push({ udid, reason: result.reason?.message ?? String(result.reason) })
  })
  return { ok, failed }
}

export async function fanoutRequests<T>(
  udids: string[],
  request: (udid: string) => Promise<T>,
): Promise<FanoutOutcome<T>> {
  return summarizeResults(await Promise.allSettled(udids.map(request)), udids)
}

export async function synchronizeStart(
  udids: string[],
  position: RuntimePoint | null,
  teleport: (lat: number, lng: number, udid: string) => Promise<unknown>,
): Promise<void> {
  if (udids.length < 2 || !position) return
  await Promise.allSettled(
    udids.map((udid) => teleport(position.lat, position.lng, udid)),
  )
  await new Promise((resolve) => setTimeout(resolve, 150))
}
