import { request } from '../../../services/api'

export interface JumpDwellSettingsResponse {
  status: string
  jump_dwell_motion: boolean
  jump_extra_wait: number
  jump_move_seconds: number
}

export const applyJumpDwellSettings = (
  enabled: boolean,
  extraWait: number,
  moveSeconds: number,
  udid?: string,
) => request<JumpDwellSettingsResponse>(
  'POST',
  '/api/location/apply-jump-settings',
  {
    jump_dwell_motion: enabled,
    jump_extra_wait: extraWait,
    jump_move_seconds: moveSeconds,
    ...(udid ? { udid } : {}),
  },
)
