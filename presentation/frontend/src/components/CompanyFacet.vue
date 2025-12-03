<template>
  <section class="company-facet">
    <header class="company-facet__header">
      <h3>{{ label }}</h3>
    </header>

    <div class="company-facet__body">
      <template v-if="isDateRange">
        <div class="company-facet__dates">
          <label>
            Início
            <input type="date" v-model="startDate" @change="onDateChange" />
          </label>
          <label>
            Fim
            <input type="date" v-model="endDate" @change="onDateChange" />
          </label>
        </div>
      </template>

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

      <template v-else>
        <div v-if="normalizedOptions.length" class="company-facet__select-wrapper">
          <input
            v-if="searchable"
            v-model="searchText"
            type="search"
            class="company-facet__search"
            placeholder="Filtrar opções…"
            @input="onSearch"
          />

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
        </div>
        <p v-else class="company-facet__empty">Nenhuma opção disponível</p>
      </template>
    </div>

    <div class="company-facet__footer">
      <select v-model="localLogical" aria-label="Operador lógico">
        <option v-for="option in logicalOptions" :key="option" :value="option">
          {{ option }}
        </option>
      </select>

      <button type="button" class="company-facet__commit" @click="commit">
        Enviar para consulta
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  field: { type: String, required: true },
  label: { type: String, required: true },
  options: { type: Array, default: () => [] },
  logical: { type: String, default: 'AND' },
  operator: { type: String, default: '' },
  values: { type: Array, default: () => [] },
  multiple: { type: Boolean, default: true },
  type: { type: String, default: 'text' },
  searchable: { type: Boolean, default: false },
})

const emit = defineEmits(['change', 'commit'])

const logicalOptions = ['AND', 'OR', 'NOT']
const localLogical = ref(props.logical || 'AND')
const localSelection = ref([])
const localBoolean = ref('')
const startDate = ref('')
const endDate = ref('')
const searchText = ref('')
const isSyncing = ref(false)

const isBoolean = computed(() => props.type === 'boolean')
const isDateRange = computed(() => props.type === 'date-range')
const isTextual = computed(() => !isBoolean.value && !isDateRange.value)

const defaultOperator = computed(() => {
  if (isDateRange.value) return 'BETWEEN'
  if (isBoolean.value) return 'EQUALS'
  return 'IN'
})

const activeOperator = computed(() => props.operator || defaultOperator.value)

const normalizedOptions = computed(() => {
  const raw = Array.isArray(props.options) ? props.options : []
  const seen = new Set()
  const entries = []
  for (const option of raw) {
    let value
    let label
    if (option && typeof option === 'object') {
      value = option.value ?? option.label ?? ''
      label = option.label ?? String(option.value ?? '')
    } else {
      value = option
      label = option
    }
    if (value === undefined || value === null || value === '') {
      continue
    }
    const key = String(value)
    if (seen.has(key)) continue
    seen.add(key)
    entries.push({ value: key, label: String(label ?? value) })
  }
  return entries
})

const filteredOptions = computed(() => {
  if (!props.searchable || !searchText.value.trim()) {
    return normalizedOptions.value
  }
  const needle = searchText.value.toLowerCase()
  return normalizedOptions.value.filter((option) =>
    option.label.toLowerCase().includes(needle)
  )
})

const computedSize = computed(() => {
  if (!isTextual.value) return 1
  const total = filteredOptions.value.length
  if (!total) return 4
  return Math.min(Math.max(total, 4), 12)
})

function currentValues() {
  if (isBoolean.value) {
    return localBoolean.value ? [localBoolean.value] : []
  }
  if (isDateRange.value) {
    const values = [startDate.value, endDate.value].filter((value) => !!value)
    if (values.length === 2) {
      return [startDate.value, endDate.value]
    }
    return []
  }
  return Array.isArray(localSelection.value)
    ? localSelection.value.map((value) => String(value))
    : []
}

function emitDraftChange() {
  if (isSyncing.value) return
  emit('change', {
    field: props.field,
    logical: localLogical.value,
    operator: activeOperator.value,
    values: currentValues(),
  })
}

function commit() {
  emit('commit', {
    field: props.field,
    logical: localLogical.value,
    operator: activeOperator.value,
    values: currentValues(),
  })
}

function onDateChange() {
  emitDraftChange()
}

function onSearch() {
  if (!searchText.value) {
    searchText.value = ''
  }
}

watch(localSelection, emitDraftChange, { deep: true })
watch(localBoolean, emitDraftChange)
watch(startDate, emitDraftChange)
watch(endDate, emitDraftChange)
watch(localLogical, emitDraftChange)

watch(
  () => props.logical,
  (value) => {
    if (value && value !== localLogical.value) {
      localLogical.value = value
    }
  }
)

watch(
  () => props.values,
  (value) => {
    isSyncing.value = true
    const incoming = Array.isArray(value) ? value.map((entry) => String(entry)) : []
    if (isBoolean.value) {
      localBoolean.value = incoming[0] ?? ''
    } else if (isDateRange.value) {
      startDate.value = incoming[0] ?? ''
      endDate.value = incoming[1] ?? ''
    } else {
      localSelection.value = [...incoming]
    }
    nextTick(() => {
      isSyncing.value = false
    })
  },
  { immediate: true }
)

watch(
  () => props.operator,
  () => {
    emitDraftChange()
  }
)

watch(
  () => props.options,
  (options) => {
    if (!isTextual.value) {
      return
    }
    const available = new Set(
      (options || []).map((option) => {
        if (option && typeof option === 'object') {
          return String(option.value ?? option.label ?? '')
        }
        return String(option ?? '')
      })
    )
    const filtered = (localSelection.value || []).filter((value) => available.has(value))
    if (filtered.length !== (localSelection.value || []).length) {
      localSelection.value = filtered
    }
  }
)
</script>

<style scoped>
.company-facet {
  border: 1px solid var(--vt-c-divider-light, #e2e8f0);
  border-radius: 8px;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background-color: var(--vt-c-bg-soft, #ffffff);
}

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

.company-facet__select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.company-facet__search {
  padding: 0.35rem 0.5rem;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
}

.company-facet__select {
  min-height: 120px;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
  padding: 0.4rem;
}

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

.company-facet__empty {
  font-size: 0.85rem;
  color: #64748b;
}

.company-facet__footer {
  display: flex;
  justify-content: flex-end;
}

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
