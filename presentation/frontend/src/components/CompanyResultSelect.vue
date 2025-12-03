<template>
  <div class="company-result-select">
    <label :for="selectId">Seleção de companhias e tickers</label>
    <select
      :id="selectId"
      multiple
      :size="computedSize"
      :disabled="disabled || !groupedOptions.length"
      v-model="localValue"
    >
      <optgroup v-for="group in groupedOptions" :key="group.company" :label="group.label">
        <option v-for="option in group.options" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </optgroup>
    </select>
    <p v-if="!groupedOptions.length" class="company-result-select__hint">
      Ajuste os filtros para listar companhias disponíveis.
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  companies: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
const selectId = `company-result-${Math.random().toString(36).slice(2, 8)}`

const localValue = computed({
  get: () => props.modelValue || [],
  set: (value) => {
    const normalized = Array.isArray(value) ? [...value] : []
    emit('update:modelValue', normalized)
  },
})

const groupedOptions = computed(() => {
  return (props.companies || [])
    .map((company) => {
      const companyName = company.company_name || ''
      const tradingName = company.trading_name || ''
      const label = tradingName && tradingName !== companyName
        ? `${companyName} — ${tradingName}`
        : companyName || 'Companhia sem nome'
      const options = (company.tickers || [])
        .filter((ticker) => !!ticker)
        .map((ticker) => ({
          value: `${companyName}::${ticker}`,
          label: `${ticker} · ${companyName}`,
        }))
      return { company: companyName || label, label, options }
    })
    .filter((group) => group.options.length > 0)
})

const computedSize = computed(() => {
  const totalOptions = groupedOptions.value.reduce((sum, group) => sum + group.options.length, 0)
  if (totalOptions === 0) return 4
  return Math.min(Math.max(totalOptions, 4), 12)
})
</script>

<style scoped>
.company-result-select {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.company-result-select label {
  font-weight: 600;
}

.company-result-select select {
  width: 100%;
  min-height: 120px;
  border-radius: 8px;
  border: 1px solid #cbd5f5;
  padding: 0.5rem;
  background-color: #fff;
}

.company-result-select__hint {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
}
</style>
