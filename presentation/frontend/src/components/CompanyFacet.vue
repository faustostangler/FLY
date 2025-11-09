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
        <select v-model="localBoolean">
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
            :multiple="isMultiple"
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

    <footer class="company-facet__footer">
      <label class="company-facet__logical">
        <span class="sr-only">Operador lógico</span>
        <select v-model="localLogical">
          <option v-for="option in logicalOptions" :key="option" :value="option">
            {{ option }}
          </option>
        </select>
      </label>

      <button type="button" class="company-facet__commit" @click="commit">
        Enviar para consulta
      </button>
    </footer>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  field: { type: String, required: true },
  label: { type: String, required: true },
  options: { type: Array, default: () => [] },
  logical: { type: String, default: 'AND' },
  operator: { type: String, default: '' },
  values: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
  multiple: { type: Boolean, default: true },
  type: { type: String, default: 'text' },
  searchable: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'commit'])

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
const isMultiple = computed(() => Boolean(props.multiple))

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
    } else if (typeof option === 'boolean') {
      value = option ? 'true' : 'false'
      label = option ? 'Sim' : 'Não'
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
    option.label.toLowerCase().includes(needle),
  )
})

const computedSize = computed(() => {
  if (!isTextual.value) return 1
  const total = filteredOptions.value.length
  if (!total) return 4
  return Math.min(Math.max(total, 4), 12)
})

function normalizeModelValue(values) {
  if (!Array.isArray(values)) {
    return []
  }
  return values
    .map((value) => String(value ?? '').trim())
    .filter((value) => value.length)
}

function syncFromModel(values) {
  const normalized = normalizeModelValue(values)
  isSyncing.value = true

  if (isBoolean.value) {
    localBoolean.value = normalized[0] || ''
  } else if (isDateRange.value) {
    startDate.value = normalized[0] || ''
    endDate.value = normalized[1] || ''
  } else if (isMultiple.value) {
    localSelection.value = [...normalized]
  } else {
    localSelection.value = normalized[0] || ''
  }

  isSyncing.value = false
}

function currentValues() {
  if (isBoolean.value) {
    return localBoolean.value ? [localBoolean.value] : []
  }

  if (isDateRange.value) {
    const values = [startDate.value, endDate.value]
      .map((v) => String(v || '').trim())
      .filter((v) => v.length)
    return values.length === 2 ? values : []
  }

  if (isMultiple.value) {
    return Array.isArray(localSelection.value)
      ? localSelection.value.map((v) => String(v ?? '').trim()).filter((v) => v.length)
      : []
  }

  const single = typeof localSelection.value === 'string'
    ? localSelection.value
    : Array.isArray(localSelection.value)
    ? localSelection.value[0]
    : ''
  const trimmed = String(single ?? '').trim()
  return trimmed ? [trimmed] : []
}

const defaultOperator = computed(() => {
  if (isDateRange.value) return 'BETWEEN'
  if (isBoolean.value) return 'EQUALS'
  return 'IN'
})

const activeOperator = computed(() => props.operator || defaultOperator.value)

watch(
  () => props.modelValue,
  (values) => {
    syncFromModel(values)
  },
  { immediate: true, deep: true },
)

watch(
  () => props.logical,
  (value) => {
    const normalized = value ? String(value).trim() : ''
    if (normalized && normalized !== localLogical.value) {
      localLogical.value = normalized
    }
  },
)

function emitSelectionChange() {
  if (isSyncing.value) return
  emit('update:modelValue', currentValues())
}

watch(localSelection, emitSelectionChange, { deep: true })
watch(localBoolean, emitSelectionChange)
watch(startDate, emitSelectionChange)
watch(endDate, emitSelectionChange)

function onDateChange() {
  emitSelectionChange()
}

function onSearch() {
  if (!searchText.value) {
    searchText.value = ''
  }
}

function commit() {
  const payload = {
    field: props.field,
    logical: localLogical.value || 'AND',
    operator: activeOperator.value,
    values: currentValues(),
  }
  emit('commit', payload)
}
</script>

<style scoped>
.company-facet {
  border: 1px solid var(--color-border, #d9d9d9);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.company-facet__header h3 {
  margin: 0;
  font-size: 1rem;
}

.company-facet__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.company-facet__select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.company-facet__search {
  padding: 6px 8px;
  border: 1px solid var(--color-border, #d9d9d9);
  border-radius: 4px;
}

.company-facet__select {
  width: 100%;
  min-height: 48px;
  border-radius: 4px;
  border: 1px solid var(--color-border, #d9d9d9);
  padding: 8px;
  font-size: 0.95rem;
}

.company-facet__empty {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

.company-facet__dates {
  display: flex;
  gap: 12px;
}

.company-facet__dates label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.9rem;
}

.company-facet__dates input {
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid var(--color-border, #d9d9d9);
}

.company-facet__footer {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.company-facet__logical select {
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid var(--color-border, #d9d9d9);
  background-color: #fff;
}

.company-facet__commit {
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid var(--primary-color, #2563eb);
  background-color: var(--primary-color, #2563eb);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.company-facet__commit:hover {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
