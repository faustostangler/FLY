<template>
  <div class="company-result-select">
    <label class="company-result-select__label">
      Resultados de companhias
      <select
        multiple
        :disabled="disabled"
        :value="modelValue"
        @change="onSelect"
      >
        <option
          v-for="company in companies"
          :key="companyKey(company)"
          :value="companyKey(company)"
        >
          {{ company.company_name }} - {{ company.tickers?.[0] || '—' }}
        </option>
      </select>
    </label>
  </div>
</template>

<script setup>
const props = defineProps({
  companies: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const companyKey = (company) => {
  const name = company.company_name || ''
  const ticker = company.tickers?.[0] || ''
  return `${name}::${ticker}`
}

const onSelect = (event) => {
  const options = Array.from(event.target.selectedOptions || [])
  emit(
    'update:modelValue',
    options.map((option) => option.value),
  )
}
</script>

<style scoped>
.company-result-select {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.company-result-select select {
  width: 100%;
  min-height: 8rem;
}
</style>
