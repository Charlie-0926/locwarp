import type { CustomModeDescriptor } from '../../contracts'
import { SpiralSettingsPanel } from './SpiralSettingsPanel'

export const SPIRAL_EXTENSION: CustomModeDescriptor = {
  id: 'spiral',
  labelKey: 'mode.spiral',
  activeState: 'spiral',
  SettingsPanel: SpiralSettingsPanel,
}

export { startSpiralRequest } from './api'
export { SpiralSettingsPanel } from './SpiralSettingsPanel'
