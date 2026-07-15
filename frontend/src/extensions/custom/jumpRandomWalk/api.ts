import { request } from '../../../services/api'

export const applyJumpRandomWalkSettings = (
  enabled: boolean,
  radius: number,
  udid?: string,
) => request<{ status: string; jump_random_walk: boolean; jump_random_walk_radius: number }>(
  'POST',
  '/api/location/apply-jump-settings',
  {
    jump_random_walk: enabled,
    jump_random_walk_radius: radius,
    ...(udid ? { udid } : {}),
  },
)
