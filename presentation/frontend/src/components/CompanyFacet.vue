<template>
  <!--
    Root section that visually groups a single facet (filter field)
    for company search. It handles three main types:
    - date-range (start/end date)
    - boolean (single select true/false-like)
    - textual (multi-select list with optional search)
  -->
  <section class="company-facet">
    <header class="company-facet__header">
      <!--
        Facet label comes from the parent and describes which field
        this facet controls (e.g., "Sector", "Country", etc.).
      -->
      <h3>{{ label }}</h3>
    </header>

    <div class="company-facet__body">
      <!--
        Branch 1: date range facet.
        Renders two date inputs (start and end) and binds them to
        local reactive refs. Changes emit draft updates to the parent.
      -->
      <template v-if="isDateRange">
        <div class="company-facet__dates">
          <label>
            Início
            <!--
              v-model keeps startDate in sync with the input value.
              @change triggers onDateChange, which emits a draft change.
            -->
            <input type="date" v-model="startDate" @change="onDateChange" />
          </label>
          <label>
            Fim
            <!--
              Same pattern for endDate: local state + change notification.
            -->
            <input type="date" v-model="endDate" @change="onDateChange" />
          </label>
        </div>
      </template>

      <!--
        Branch 2: boolean facet.
        Renders a simple single-select with a "Select..." placeholder.
        Options are normalized into { value, label } pairs.
      -->
      <template v-else-if="isBoolean">
        <select v-model="localBoolean" @change="emitDraftChange">
          <option value="">Selecione…</option>
          <option
            v-for="option in normalizedOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </template>

      <!--
        Branch 3: textual facet (default).
        Supports:
        - optional search box for filtering options by label
        - single or multi-select depending on 'multiple' prop
      -->
      <template v-else>
        <div v-if="normalizedOptions.length" class="company-facet__select-wrapper">
          <!--
            Optional search input.
            When 'searchable' is true, user text is stored in searchText
            and used by filteredOptions to narrow the available choices.
          -->
          <input
            v-if="searchable"
            v-model="searchText"
            type="search"
            class="company-facet__search"
            placeholder="Filtrar opções…"
            @input="onSearch"
          />

          <!--
            Select element showing the normalized & filtered options.
            - v-model is bound to localSelection (array for multi-select)
            - :multiple toggles single vs multi-select behavior
            - :size adapts the visual height of the list to option count
          -->
          <select
            v-model="localSelection"
            :multiple="multiple"
            class="company-facet__select"
            :size="computedSize"
          >
            <option
              v-for="option in filteredOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>

          <ul v-if="localSelection.length" class="company-facet__chips">
            <li v-for="value in localSelection" :key="value" class="company-facet__chip">
              <span>{{ labelFor(value) }}</span>
              <button
                type="button"
                class="company-facet__chip-remove"
                :aria-label="`Remover filtro ${labelFor(value)}`"
                @click="removeValue(value)"
              >
                ×
              </button>
            </li>
          </ul>

          <button
            v-if="localSelection.length"
            type="button"
            class="company-facet__clear"
            @click="clearFacet"
          >
            Limpar {{ label }}
          </button>
        </div>
        <!--
          Fallback shown when there are no options available for this facet.
        -->
        <p v-else class="company-facet__empty">Nenhuma opção disponível</p>
      </template>
    </div>

    <!--
      Footer section:
      - logical operator (AND/OR/NOT) selector
      - explicit "commit" button that sends the current state to the parent
    -->
    <div class="company-facet__footer">
      <button type="button" class="company-facet__commit" @click="commit">
        Aplicar
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'

/**
 * Props contract for the CompanyFacet component.
 * Each prop is intentionally small and declarative, so the component
 * can be reused for different fields without knowing business details.
 */
const props = defineProps({
  // Field identifier used by the parent to map this facet to a domain field.
  field: { type: String, required: true },
  // Human-readable label shown in the facet header.
  label: { type: String, required: true },
  // Raw options provided by the parent, can be primitives or objects.
  options: { type: Array, default: () => [] },
  // Logical operator (AND, OR, NOT) used to combine this facet with others.
  logical: { type: String, default: 'AND' },
  // Explicit operator for this facet (IN, BETWEEN, EQUALS, etc.).
  operator: { type: String, default: '' },
  // Current selected values as provided by the parent.
  values: { type: Array, default: () => [] },
  // Controls whether the select accepts multiple values or a single one.
  multiple: { type: Boolean, default: true },
  // High-level type that controls which UI is rendered.
  // Expected values: 'text' | 'boolean' | 'date-range'.
  type: { type: String, default: 'text' },
  // Enables the local search box when true (for textual facets).
  searchable: { type: Boolean, default: false },
})

/**
 * Set of events emitted to the parent:
 * - 'change': draft change whenever the user modifies local state
 * - 'commit': explicit confirmation when user clicks the commit button
 */
const emit = defineEmits(['change', 'commit'])

// Logical operator is fixed to AND for simple facet composition.
const localLogical = ref('AND')

// Local selection used for textual facets (single or multiple values).
const localSelection = ref([])

// Local single value used for boolean facets.
const localBoolean = ref('')

// Local date inputs for date-range facets.
const startDate = ref('')
const endDate = ref('')

// Text used to filter available options in the textual facet.
const searchText = ref('')

// Guard flag to prevent feedback loops when syncing from props to local state.
const isSyncing = ref(false)

/**
 * Type helpers to simplify conditional rendering and logic.
 */
const isBoolean = computed(() => props.type === 'boolean')
const isDateRange = computed(() => props.type === 'date-range')
const isTextual = computed(() => !isBoolean.value && !isDateRange.value)

/**
 * Default operator when the parent does not explicitly pass one.
 * - date-range => BETWEEN
 * - boolean    => EQUALS
 * - textual    => IN
 */
const defaultOperator = computed(() => {
  if (isDateRange.value) return 'BETWEEN'
  if (isBoolean.value) return 'EQUALS'
  return 'IN'
})

/**
 * Active operator that this facet will use for its outgoing payload.
 * Prefers the explicit prop; falls back to type-based default.
 */
const activeOperator = computed(() => props.operator || defaultOperator.value)

/**
 * Normalize the incoming options into a stable list of
 * { value: string, label: string } objects with:
 * - defensive checks for missing/null values
 * - de-duplication by 'value' to keep the list consistent
 */
const normalizedOptions = computed(() => {
  // Defensive: ensure we always iterate over an array.
  const raw = Array.isArray(props.options) ? props.options : []

  // Keep track of which values we have already emitted to avoid duplicates.
  const seen = new Set()
  const entries = []

  // Walk through the raw options and normalize each entry.
  for (const option of raw) {
    let value
    let label

    // Case 1: object-like option, e.g. { value: 'BR', label: 'Brazil' }.
    if (option && typeof option === 'object') {
      // Prefer 'value' and fall back to 'label'; default to empty string.
      value = option.value ?? option.label ?? ''
      // Prefer 'label' and fall back to the stringified value.
      label = option.label ?? String(option.value ?? '')
    } else {
      // Case 2: primitive option (string, number, etc.).
      value = option
      label = option
    }

    // Ignore undefined/null/empty values to keep the UI clean.
    if (value === undefined || value === null || value === '') {
      continue
    }

    // Use a string key to unify comparisons and de-duplication.
    const key = String(value)
    if (seen.has(key)) continue

    // Mark this value as seen and push the normalized entry.
    seen.add(key)
    entries.push({ value: key, label: String(label ?? value) })
  }

  return entries
})

/**
 * Filtered list of options based on searchText.
 * When 'searchable' is false or the search text is empty, fall back to
 * the full normalized options list.
 */
const filteredOptions = computed(() => {
  // No search requested: return all normalized options.
  if (!props.searchable || !searchText.value.trim()) {
    return normalizedOptions.value
  }

  // Normalize search needle to lowercase for case-insensitive matching.
  const needle = searchText.value.toLowerCase()

  // Return only options whose label contains the search substring.
  return normalizedOptions.value.filter((option) =>
    option.label.toLowerCase().includes(needle)
  )
})

/**
 * Compute the select's 'size' attribute dynamically from the number
 * of filtered options, within a reasonable min/max window:
 * - minimum rows: 4
 * - maximum rows: 12
 * This keeps the UI usable for both short and long lists.
 */
const computedSize = computed(() => {
  // Non-textual facets do not use a resizable multi-select.
  if (!isTextual.value) return 1

  const total = filteredOptions.value.length

  // If there are no options, still show a small list height.
  if (!total) return 4

  // Clamp the height between 4 and 12 lines.
  return Math.min(Math.max(total, 4), 12)
})

/**
 * Helper that generates the current values array according to the facet type.
 * The result is always an array of strings, ready to be sent to the parent.
 */
function currentValues() {
  // Boolean facet: return a single value (if any) wrapped in an array.
  if (isBoolean.value) {
    return localBoolean.value ? [localBoolean.value] : []
  }

  // Date-range facet: only emit when both boundaries are present.
  if (isDateRange.value) {
    const values = [startDate.value, endDate.value].filter((value) => !!value)
    if (values.length === 2) {
      // Both dates provided: return them in [start, end] order.
      return [startDate.value, endDate.value]
    }
    // Incomplete range: treat as "no selection" from the perspective of the caller.
    return []
  }

  // Textual facet: ensure we always return an array of strings.
  const rawValues = Array.isArray(localSelection.value)
    ? localSelection.value.map((value) => String(value))
    : []

  const seen = new Set()
  const uniqueValues = []
  for (const value of rawValues) {
    if (!value) continue
    if (seen.has(value)) continue
    seen.add(value)
    uniqueValues.push(value)
  }
  return uniqueValues
}

/**
 * Emit a "change" event with the current draft state of the facet.
 * It is used for real-time updates while the user is editing.
 * The isSyncing guard prevents infinite loops when syncing from props.
 */
function emitDraftChange() {
  if (isSyncing.value) return

  emit('change', {
    field: props.field,
    logical: localLogical.value,
    operator: activeOperator.value,
    values: currentValues(),
  })
}

/**
 * Emit a "commit" event when the user explicitly confirms the facet.
 * The payload mirrors the 'change' event but indicates a deliberate action.
 */
function commit() {
  emit('commit', {
    field: props.field,
    logical: localLogical.value,
    operator: activeOperator.value,
    values: currentValues(),
  })
}

/**
 * Handler for date inputs.
 * Delegates directly to the draft-change emitter to keep behavior consistent.
 */
function onDateChange() {
  emitDraftChange()
}

/**
 * Handler for the search input.
 * Ensures that searchText never drifts into non-string/undefined values.
 */
function onSearch() {
  if (!searchText.value) {
    // Normalize falsy values back to an empty string.
    searchText.value = ''
  }
}

function removeValue(valueToRemove) {
  localSelection.value = (localSelection.value || []).filter((value) => value !== valueToRemove)
  emitDraftChange()
  commit()
}

function clearFacet() {
  localSelection.value = []
  emitDraftChange()
  commit()
}

function labelFor(value) {
  const option = normalizedOptions.value.find((entry) => entry.value === value)
  return option?.label ?? String(value)
}

/**
 * Watchers that keep the parent informed whenever local state changes.
 * These represent the "user is editing" flow and feed the 'change' event.
 */

// When the textual selection changes (including deep array mutations),
// emit a draft update.
watch(localSelection, emitDraftChange, { deep: true })

// Boolean facet: keep parent in sync whenever the single value changes.
watch(localBoolean, emitDraftChange)

// Date-range facet: emit drafts whenever either boundary changes.
watch(startDate, emitDraftChange)
watch(endDate, emitDraftChange)

/**
 * Sync local selection state whenever the parent updates the 'values' prop.
 * This is a one-way, top-down synchronization:
 * - mark isSyncing to avoid emitting feedback on this change
 * - adapt behavior to the facet type (boolean, date-range, textual)
 */
watch(
  () => props.values,
  (value) => {
    // Guard against recursive updates while we are applying incoming props.
    isSyncing.value = true

    // Normalize incoming entries as strings for consistent comparison.
    const incoming = Array.isArray(value) ? value.map((entry) => String(entry)) : []

    if (isBoolean.value) {
      // Boolean facet: take the first value (or empty) as the local selection.
      localBoolean.value = incoming[0] ?? ''
    } else if (isDateRange.value) {
      // Date-range facet: map to start and end dates.
      startDate.value = incoming[0] ?? ''
      endDate.value = incoming[1] ?? ''
    } else {
      // Textual facet: clone the incoming values into localSelection.
      localSelection.value = [...incoming]
    }

    // Release the sync guard on the next microtask to allow normal events again.
    nextTick(() => {
      isSyncing.value = false
    })
  },
  { immediate: true }
)

/**
 * Whenever the 'operator' prop changes from the parent,
 * refresh the draft payload so the parent sees a consistent snapshot
 * (field + logical + new operator + current values).
 */
watch(
  () => props.operator,
  () => {
    emitDraftChange()
  }
)

/**
 * When the available options list changes (e.g., after an async fetch),
 * ensure the current textual selections are still valid.
 * Any local value that is no longer in the available set is removed.
 */
watch(
  () => props.options,
  (options) => {
    // Only textual facets rely on options; skip for boolean/date-range.
    if (!isTextual.value) {
      return
    }

    // Build a set of currently available option values, normalized to strings.
    const available = new Set(
      (options || []).map((option) => {
        if (option && typeof option === 'object') {
          return String(option.value ?? option.label ?? '')
        }
        return String(option ?? '')
      })
    )

    // Retain only local selections that still exist in the available options.
    const filtered = (localSelection.value || []).filter((value) => available.has(value))

    // Only update localSelection when something actually changed.
    if (filtered.length !== (localSelection.value || []).length) {
      localSelection.value = filtered
    }
  }
)
</script>

<style scoped>
/* Root container styling: visual card around a single facet. */
.company-facet {
  border: 1px solid var(--vt-c-divider-light, #e2e8f0);
  border-radius: 8px;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background-color: var(--vt-c-bg-soft, #ffffff);
}

/* Header: aligns the facet title and any potential future controls. */
.company-facet__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.company-facet__header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.company-facet__header select {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

/* Body: vertical stack of the facet controls (dates, select, search, etc.). */
.company-facet__body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.company-facet__body select {
  padding: 0.35rem 0.5rem;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
}

/* Wrapper used by textual facets to stack search input and select element. */
.company-facet__select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

/* Search input styling for filtering options. */
.company-facet__search {
  padding: 0.35rem 0.5rem;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
}

/* Main select styling for textual facets (multi or single). */
.company-facet__select {
  min-height: 120px;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
  padding: 0.4rem;
}

.company-facet__chips {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  padding: 0;
  margin: 0;
}

.company-facet__chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: #edf2ff;
  border: 1px solid #cbd5f5;
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
}

.company-facet__chip-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  color: #334155;
}

.company-facet__clear {
  align-self: flex-start;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
  background-color: #ffffff;
  cursor: pointer;
}

/* Layout for the two date inputs (start and end) in a grid. */
.company-facet__dates {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
}

.company-facet__dates label {
  display: flex;
  flex-direction: column;
  font-size: 0.85rem;
  gap: 0.25rem;
}

.company-facet__dates input[type='date'] {
  padding: 0.35rem 0.5rem;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
}

/* Empty state text when no options exist for a textual facet. */
.company-facet__empty {
  font-size: 0.85rem;
  color: #64748b;
}

/* Footer aligns the logical operator selector and commit button. */
.company-facet__footer {
  display: flex;
  justify-content: flex-end;
}

/* Commit button: primary action to send the facet state to the parent. */
.company-facet__commit {
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--vt-c-primary, #2563eb);
  background-color: var(--vt-c-primary, #2563eb);
  color: #ffffff;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.company-facet__commit:hover {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
}
</style>
