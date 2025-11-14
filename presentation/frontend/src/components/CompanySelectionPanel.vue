<template>
  <section
    v-if="hasSelection"
    class="home__selected-companies"
    aria-labelledby="selected-companies-heading"
  >
    <h3 id="selected-companies-heading">Empresas selecionadas</h3>

    <table class="home__selected-table">
      <thead>
        <tr>
          <th scope="col">Companhia</th>
          <th scope="col">Ticker</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="pair in safePairs"
          :key="`${pair.company}::${pair.ticker}`"
        >
          <td>{{ pair.company }}</td>
          <td>{{ pair.ticker }}</td>
        </tr>
      </tbody>
    </table>

    <div class="home__selected-actions-bar">
      <button
        type="button"
        class="home__charts-button"
        :disabled="!hasSelection"
        @click="emitVisualizarGraficos"
      >
        Visualizar Gráficos
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  selectedPairs: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['visualizar-graficos'])

const safePairs = computed(() =>
  Array.isArray(props.selectedPairs) ? props.selectedPairs : [],
)

const hasSelection = computed(() => safePairs.value.length > 0)

const emitVisualizarGraficos = () => {
  emit('visualizar-graficos')
}
</script>

<style scoped>
.home__selected-companies {
  display: grid;
  gap: 0.75rem;
}

.home__selected-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
}

.home__selected-table th,
.home__selected-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.home__selected-table tbody tr:last-child td {
  border-bottom: none;
}

.home__selected-actions-bar {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-end;
}

.home__charts-button {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s ease;
}

.home__charts-button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.home__charts-button:not(:disabled):hover {
  background: #1d4ed8;
}
</style>
