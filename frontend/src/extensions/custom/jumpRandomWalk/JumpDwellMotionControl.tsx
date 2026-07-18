import React from 'react'

interface Props {
  enabled: boolean
  extraWait: number
  moveSeconds: number
  running: boolean
  onEnabledChange?: (enabled: boolean) => void
  onExtraWaitChange?: (seconds: number) => void
  onMoveSecondsChange?: (seconds: number) => void
  onApply?: () => Promise<void> | void
  t: (key: any, vars?: Record<string, string | number>) => string
}

export const JumpDwellMotionControl: React.FC<Props> = ({
  enabled,
  extraWait,
  moveSeconds,
  running,
  onEnabledChange,
  onExtraWaitChange,
  onMoveSecondsChange,
  onApply,
  t,
}) => {
  const totalSeconds = extraWait + (enabled ? moveSeconds : 0)

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8, width: '100%' }}>
      <label
        title={t('panel.jump_extra_wait_tooltip')}
        style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, opacity: 0.85 }}
      >
        {t('panel.jump_extra_wait')}
        <input
          type="number"
          step="0.5"
          min="0"
          value={extraWait}
          onChange={(event) => {
            const value = parseFloat(event.target.value)
            if (Number.isFinite(value) && value >= 0) onExtraWaitChange?.(value)
          }}
          style={{
            width: 60, padding: '2px 6px', fontSize: 11,
            background: '#0f1218', color: '#e6e8ee',
            border: '1px solid rgba(255,255,255,0.12)', borderRadius: 4,
          }}
        />
        <span style={{ opacity: 0.7 }}>{t('panel.jump_delay_seconds')}</span>
      </label>

      <label
        className="lw-checkbox"
        title={t('panel.jump_dwell_motion_tooltip')}
        style={{ fontSize: 11, padding: 0, background: 'transparent', border: 'none' }}
      >
        <input
          type="checkbox"
          checked={enabled}
          onChange={(event) => onEnabledChange?.(event.target.checked)}
        />
        <span className="lw-checkbox-box" />
        <span className="lw-checkbox-label" style={{ lineHeight: 1.15 }}>
          {t('panel.jump_dwell_motion')}
        </span>
      </label>

      <label
        title={t('panel.jump_move_seconds_tooltip')}
        style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, opacity: enabled ? 0.85 : 0.5 }}
      >
        {t('panel.jump_move_seconds')}
        <input
          type="number"
          step="0.5"
          min="0"
          value={moveSeconds}
          disabled={!enabled}
          onChange={(event) => {
            const value = parseFloat(event.target.value)
            if (Number.isFinite(value) && value >= 0) onMoveSecondsChange?.(value)
          }}
          style={{
            width: 60, padding: '2px 6px', fontSize: 11,
            background: '#0f1218', color: '#e6e8ee',
            border: '1px solid rgba(255,255,255,0.12)', borderRadius: 4,
          }}
        />
        <span style={{ opacity: 0.7 }}>{t('panel.jump_delay_seconds')}</span>
      </label>

      <div style={{ width: '100%', fontSize: 10, lineHeight: 1.35, opacity: 0.68 }}>
        {enabled
          ? t('panel.jump_dwell_total_enabled', { n: extraWait, m: moveSeconds, total: totalSeconds })
          : t('panel.jump_dwell_total_disabled', { n: extraWait })}
      </div>

      {running && onApply && (
        <button
          className="action-btn primary"
          style={{ width: '100%', padding: '4px 8px', fontSize: 11 }}
          onClick={() => onApply()}
        >
          {t('panel.apply_jump_settings')}
        </button>
      )}
    </div>
  )
}
