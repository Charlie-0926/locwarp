import React from 'react'

interface Props {
  radius: number
  spacing: number
  onRadiusChange: (value: number) => void
  onSpacingChange: (value: number) => void
  t: (key: any) => string
}

export const SpiralSettingsPanel: React.FC<Props> = ({
  radius, spacing, onRadiusChange, onSpacingChange, t,
}) => (
  <div className="section" style={{ margin: '0 0 8px 0' }}>
    <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 12c0-3 4-3 4 0s-4 5-7 3-3-8 2-10 9 2 9 8-6 10-13 7" />
      </svg>
      {t('mode.spiral')}
    </div>
    <div className="section-content">
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 8 }}>
        <div style={{ width: 100, fontSize: 12 }}>{t('panel.spiral_radius')}</div>
        <input type="number" className="search-input" value={radius}
          onChange={(event) => {
            const value = parseInt(event.target.value)
            if (!isNaN(value) && value > 0) onRadiusChange(value)
          }} style={{ flex: 1 }} min="10" step="50" />
      </div>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        <div style={{ width: 100, fontSize: 12 }}>{t('panel.spiral_spacing')}</div>
        <input type="number" className="search-input" value={spacing}
          onChange={(event) => {
            const value = parseInt(event.target.value)
            if (!isNaN(value) && value > 0) onSpacingChange(value)
          }} style={{ flex: 1 }} min="5" step="5" />
      </div>
    </div>
  </div>
)
