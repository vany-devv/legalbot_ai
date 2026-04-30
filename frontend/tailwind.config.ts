import type { Config } from 'tailwindcss'

export default {
  content: [
    './app.vue',
    './components/**/*.vue',
    './pages/**/*.vue',
    './layouts/**/*.vue',
    './composables/**/*.ts',
  ],
  theme: {
    extend: {
      colors: {
        // ── Surfaces ─────────────────────────────────────────
        canvas:  'var(--bg-canvas)',
        panel:   'var(--bg-panel)',
        raised:  'var(--bg-raised)',
        dimmed:  'var(--bg-hover)',
        sidebar: 'var(--bg-sidebar)',
        field:   'var(--bg-input)',
        cite:    'var(--bg-citation)',

        // ── Borders ──────────────────────────────────────────
        rim:         'var(--border)',
        'rim-faint': 'var(--border-faint)',
        'rim-strong':'var(--border-strong)',

        // ── Text ─────────────────────────────────────────────
        ink:         'var(--text-primary)',
        'ink-muted': 'var(--text-secondary)',
        'ink-faint': 'var(--text-tertiary)',

        // ── Brand (palette-driven scale) ─────────────────────
        brand: {
          DEFAULT: 'var(--accent)',
          lit:     'var(--accent-hover)',
          dim:     'var(--accent-subtle)',
          on:      'var(--accent-on)',
          50:  'var(--brand-50)',
          100: 'var(--brand-100)',
          200: 'var(--brand-200)',
          300: 'var(--brand-300)',
          400: 'var(--brand-400)',
          500: 'var(--brand-500)',
          600: 'var(--brand-600)',
          700: 'var(--brand-700)',
          800: 'var(--brand-800)',
          900: 'var(--brand-900)',
        },
        'brand-lit': 'var(--accent-hover)',
        'brand-dim': 'var(--accent-subtle)',

        // ── Status ───────────────────────────────────────────
        danger:  'var(--danger)',
        warning: 'var(--warning)',
        ok:      'var(--success)',
        info:    'var(--info)',
      },
      fontFamily: {
        sans:    ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        display: ['Manrope', 'Inter', '-apple-system', 'sans-serif'],
        mono:    ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        xs:  'var(--radius-xs)',
        sm:  'var(--radius-sm)',
        md:  'var(--radius-md)',
        lg:  'var(--radius-lg)',
        xl:  'var(--radius-xl)',
      },
      boxShadow: {
        'soft':   'var(--shadow-sm)',
        'medium': 'var(--shadow-md)',
        'high':   'var(--shadow-lg)',
      },
      transitionTimingFunction: {
        'out-soft': 'cubic-bezier(0.2, 0.7, 0.2, 1)',
        'spring':   'cubic-bezier(0.34, 1.3, 0.64, 1)',
      },
    },
  },
  plugins: [],
} satisfies Config
