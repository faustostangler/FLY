<template>
  <section class="company-facet">
    <header class="company-facet__header">
      <h3>{{ label }}</h3>
      <select v-model="localLogical" aria-label="Operador lógico">
        <option v-for="option in logicalOptions" :key="option" :value="option">
          {{ option }}
        </option>
      </select>
    </header>
    <div v-if="!options.length" class="company-facet__empty">
      Nenhuma opção disponível
    </div>
    <ul v-else class="company-facet__options">
      <li v-for="option in options" :key="option">
        <label>
          <input
            :type="multiple ? 'checkbox' : 'radio'"
            :name="field"
            :value="option"
            :checked="isSelected(option)"
            @change="toggle(option)"
          />
          <span>{{ option }}</span>
        </label>
      </li>
    </ul>
    <div v-if="options.length" class="company-facet__footer">
      <button type="button" class="company-facet__commit" @click="commit">
        Enviar para consulta
      </button>
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  field: { type: String, required: true },
  label: { type: String, required: true },
  options: { type: Array, default: () => [] },
  logical: { type: String, default: 'AND' },
  values: { type: Array, default: () => [] },
  multiple: { type: Boolean, default: true },
})

const emit = defineEmits(['change', 'commit'])

const logicalOptions = ['AND', 'OR', 'NOT']
const localLogical = ref(props.logical || 'AND')
const selected = ref([...props.values])

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
    const incoming = Array.isArray(value) ? [...value] : []
    if (JSON.stringify(incoming) !== JSON.stringify(selected.value)) {
      selected.value = incoming
    }
  }
)

function isSelected(option) {
  return selected.value.includes(option)
}

function toggle(option) {
  const exists = selected.value.includes(option)
  if (props.multiple) {
    if (exists) {
      selected.value = selected.value.filter((value) => value !== option)
    } else {
      selected.value = [...selected.value, option]
    }
  } else {
    selected.value = exists ? [] : [option]
  }
  emitDraftChange()
}

function emitDraftChange() {
  emit('change', {
    field: props.field,
    logical: localLogical.value,
    values: [...selected.value],
  })
}

function commit() {
  emit('commit', {
    field: props.field,
    logical: localLogical.value,
    values: [...selected.value],
  })
}

watch(localLogical, () => emitDraftChange())

watch(
  () => props.options,
  (options) => {
    const normalized = new Set(options)
    const filtered = selected.value.filter((value) => normalized.has(value))
    if (filtered.length !== selected.value.length) {
      selected.value = filtered
      emitDraftChange()
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
  gap: 0.5rem;
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

.company-facet__options {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.25rem 0.75rem;
  max-height: 200px;
  overflow-y: auto;
}

.company-facet__options label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
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
