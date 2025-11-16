<template>
  <section class="company-facet">
    <header class="company-facet__header">
      <h3>{{ label }}</h3>
    </header>

    <div class="company-facet__body">
      <div v-if="options.length" class="company-facet__select-wrapper">
        <input
          v-if="searchable"
          v-model="searchText"
          type="search"
          class="company-facet__search"
          placeholder="Filtrar opções…"
        />

        <select
          v-model="localValue"
          :multiple="multiple"
          class="company-facet__select"
          :size="computedSize"
        >
          <option
            v-for="option in filteredOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }} <span v-if="option.count">({{ option.count }})</span>
          </option>
        </select>
      </div>
      <p v-else class="company-facet__empty">Nenhuma opção disponível</p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  facetKey: { type: String, required: true },
  label: { type: String, required: true },
  options: { type: Array, required: true },
  modelValue: { type: Array, default: () => [] },
  multiple: { type: Boolean, default: true },
  searchable: { type: Boolean, default: false },
  type: { type: String, default: 'select' },
})

const emit = defineEmits(['update:modelValue'])

const searchText = ref('')

const normalizedOptions = computed(() => {
  return (props.options || []).map((option) => ({
    value: option.value ?? option.label ?? '',
    label: option.label ?? String(option.value ?? ''),
    count: option.count,
  }))
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

const localValue = computed({
  get: () => props.modelValue || [],
  set: (value) => {
    const normalized = Array.isArray(value) ? value : [value].filter(Boolean)
    emit('update:modelValue', normalized)
  },
})

const computedSize = computed(() => {
  const total = filteredOptions.value.length
  if (!total) return 4
  return Math.min(Math.max(total, 4), 12)
})

watch(
  () => props.modelValue,
  (value) => {
    if (!Array.isArray(value)) {
      emit('update:modelValue', [])
    }
  },
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

.company-facet__body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
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

.company-facet__empty {
  font-size: 0.85rem;
  color: #64748b;
}
</style>
