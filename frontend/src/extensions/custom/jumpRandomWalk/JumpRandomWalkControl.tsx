import React from 'react'

interface Props {
  enabled: boolean
  radius: number
  running: boolean
  onEnabledChange?: (enabled: boolean) => void
  onRadiusChange?: (radius: number) => void
  onApply?: () => Promise<void> | void
  t: (key: any) => string
}

export const JumpRandomWalkControl: React.FC<Props> = ({
  enabled,
  radius,
  running,
  onEnabledChange,
  onRadiusChange,
  onApply,
  t,
}) => (
  <>
    <label
      className="lw-checkbox"
      title={t('panel.jump_random_walk_tooltip')}
      style={{ fontSize: 11, padding: 0, background: 'transparent', border: 'none', marginLeft: 10 }}
    >
      <input
        type="checkbox"
        checked={enabled}
        onChange={(event) => onEnabledChange?.(event.target.checked)}
      />
      <span className="lw-checkbox-box" />
      <span className="lw-checkbox-label" style={{ lineHeight: 1.15 }}>
        {t('panel.jump_random_walk')}
      </span>
    </label>
    {enabled && (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, opacity: 0.85, width: '100%', marginTop: 5 }}>
        {t('panel.random_walk_range')}
        <input
          type="number"
          step="1"
          min="0"
          value={radius}
          onChange={(event) => {
            const value = parseFloat(event.target.value)
            if (Number.isFinite(value) && value >= 0) onRadiusChange?.(value)
          }}
          style={{
            width: 60, padding: '2px 6px', fontSize: 11,
            background: '#0f1218', color: '#e6e8ee',
            border: '1px solid rgba(255,255,255,0.12)', borderRadius: 4,
          }}
        />
        <span style={{ opacity: 0.7 }}>{t('panel.meters_radius')}</span>
      </span>
    )}
    {running && onApply && (
      <button
        className="action-btn primary"
        style={{ width: '100%', padding: '4px 8px', fontSize: 11, marginTop: 5 }}
        onClick={() => onApply()}
      >
        {t('panel.apply_speed')}
      </button>
    )}
  </>
)
