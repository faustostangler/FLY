<template>
  <fieldset class="company-facet">
    <legend>{{ label }}</legend>
    <div class="company-facet__options">
      <label
        v-for="option in options"
        :key="option.value || option"
        class="company-facet__option"
      >
        <input
          type="checkbox"
          :value="option.value || option"
          :checked="values.includes(option.value || option)"
          @change="onToggle(option.value || option)"
        />
        <span>{{ option.label || option }}</span>
      </label>
    </div>
  </fieldset>
</template>

<script setup>
const props = defineProps({
  field: { type: String, required: true },
  label: { type: String, required: true },
  options: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  logical: { type: String, default: 'AND' },
  multiple: { type: Boolean, default: true },
})

const emit = defineEmits(['change'])

const onToggle = (value) => {
  emit('change', {
    field: props.field,
    value,
  })
}
</script>

<style scoped>
.company-facet {
  border: 1px solid #e0e0e0;
  padding: 1rem;
  border-radius: 0.5rem;
}

.company-facet__options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.company-facet__option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
