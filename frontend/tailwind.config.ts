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
        // Backgrounds — mapped to CSS vars for dark/light theme switching
        canvas:  'var(--bg-primary)',
        panel:   'var(--bg-secondary)',
        raised:  'var(--bg-tertiary)',
        dimmed:  'var(--bg-hover)',
        sidebar: 'var(--bg-sidebar)',
        field:   'var(--bg-input)',
        cite:    'var(--bg-citation)',
        // Borders
        rim:       'var(--border)',
        'rim-faint': 'var(--border-light)',
        // Text
        ink:       'var(--text-primary)',
        'ink-muted': 'var(--text-secondary)',
        'ink-faint': 'var(--text-tertiary)',
        // Brand (indigo)
        brand:     'var(--accent)',
        'brand-lit': 'var(--accent-hover)',
        'brand-dim': 'var(--accent-subtle)',
        // Status
        danger:  'var(--danger)',
        warning: 'var(--warning)',
        ok:      'var(--success)',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Inter', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
