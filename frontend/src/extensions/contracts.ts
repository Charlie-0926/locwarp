import type React from 'react'

export interface CustomModeDescriptor {
  id: string
  labelKey: string
  activeState: string
  SettingsPanel: React.ComponentType<any>
}
