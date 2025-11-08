<template>
  <div class="chart-selector">
    <label>
      Tipo de gráfico
      <select v-model="selected">
        <option value="price">Preço</option>
        <option value="volume">Volume</option>
      </select>
    </label>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const selected = ref('price')
</script>

<style scoped>
.chart-selector {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
</style>
