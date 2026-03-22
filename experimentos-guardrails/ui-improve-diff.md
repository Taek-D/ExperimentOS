# UI Improve — Unapplied MINOR Items

These items were identified during the Phase 3 audit but not applied.
Apply them manually if desired.

## m1: Inconsistent opacity text (text-white/35 vs text-white/40)

Several components use `text-white/35` while the standard dim text is `text-white/40`.
Search for `text-white/35` and evaluate whether to unify to `text-white/40`.

Affected files: Dashboard.tsx, ContinuousMetrics.tsx, PowerCalculator.tsx, MetricsTable.tsx

## m2: Status badge class duplication

In `index.css`, the 4 status-badge variants (`-critical`, `-warning`, `-positive`, `-neutral`)
all repeat the same `@apply` base. Extract a shared `.status-badge-base` class.

```diff
- .status-badge-critical {
-   @apply inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-colors cursor-default;
-   ...
- }
+ .status-badge-base {
+   @apply inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-colors cursor-default;
+ }
+ .status-badge-critical { @extend .status-badge-base; ... }
```

## m3: Dark mode select styling

`<select>` elements use browser-default dropdown styling which looks out of place
in the dark theme. Consider a custom dropdown component or CSS overrides:

```css
select {
  appearance: none;
  background-image: url("data:image/svg+xml,...chevron...");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
}
option {
  background: var(--color-surface-1);
  color: white;
}
```

Affected: IntegrationConnect.tsx, ExperimentSelector.tsx, SequentialMonitor.tsx

## m4: Status badge text size

`text-[10px]` (10px) is below comfortable reading size.
Consider bumping to `text-[11px]` for better readability.

## m5: Inconsistent gap values

Similar card groups use `gap-3`, `gap-4`, `gap-5` interchangeably.
Standardize: `gap-3` for tight groups, `gap-4` for standard, `gap-6` for sections.

## m6: Long transition durations

Some elements use `duration-500` (500ms). For most UI transitions, 200-300ms is preferred.
Search for `duration-500` and evaluate reducing to `duration-300`.
