import type { CustomModeDescriptor } from './contracts'
import { SPIRAL_EXTENSION } from './custom/spiral'

export const CUSTOM_MODE_EXTENSIONS: readonly CustomModeDescriptor[] = [
  SPIRAL_EXTENSION,
]

export const customModeById = (id: string) =>
  CUSTOM_MODE_EXTENSIONS.find((extension) => extension.id === id)
