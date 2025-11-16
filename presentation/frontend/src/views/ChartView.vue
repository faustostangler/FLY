<!-- src/views/ChartView.vue -->
<template>
  <section class="chart-view">
    <!-- 1) Cabeçalho -->
    <!-- Step 1: Static header describing the current view -->
    <header class="chart-header">
      <h1>Gráfico</h1>
    </header>

    <!-- 2) Estado de loading -->
    <!-- Step 2: Show loading state while the chart data is being fetched -->
    <div v-if="isLoading" class="chart-loading">
      Carregando gráfico...
    </div>

    <!-- 3) Erro da API -->
    <!-- Step 3: If an API error occurred, surface a human-readable message -->
    <div v-else-if="error" class="chart-error">
      {{ error }}
    </div>

    <!-- 4) Nenhum ticker selecionado -->
    <!-- Step 4: Guardrail when the user has not selected a company/ticker yet -->
    <div v-else-if="!hasTicker">
      Escolha uma companhia para visualizar o gráfico.
    </div>

    <!-- 5) Nenhum dado ainda -->
    <!-- Step 5: A ticker exists, but no chart data was loaded or requested yet -->
    <div v-else-if="!chart">
      Nenhum gráfico carregado ainda.
    </div>

    <!-- 6) Gráfico Plotly -->
    <!-- Step 6: Successful case – render the Plotly chart widget with the DTO payload -->
    <div v-else class="chart-container">
      <VuePlotly
        :data="chart.data"
        :layout="chart.layout"
        :config="plotConfig"
      />
      <!-- Acessibilidade: descrição textual do gráfico -->
      <!-- Accessibility: textual description so screen readers can announce the chart meaning -->
      <div
        role="img"
        aria-label="Gráfico de dados de mercado gerado a partir da API FLY"
      ></div>
    </div>
  </section>
</template>

<script setup>
/**
 * ChartView.vue
 *
 * Presentation-layer route component for displaying a single Plotly chart.
 * This component:
 * - Reads the current chart DTO and loading/error flags from the Pinia store.
 * - Chooses which visual state to show (loading, error, empty, or chart).
 * - Triggers an initial chart load on mount when the route already defines a type.
 *
 * Domain-agnostic responsibilities:
 * - Does not implement business rules; it only orchestrates UI states.
 * - Delegates all data fetching and chart construction to the chart Pinia store.
 */

import { onMounted, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useChartStore } from '../store/chartStore'

/**
 * Pinia chart store instance.
 *
 * The store encapsulates:
 * - ChartDTO state (data/layout),
 * - parameters used to query the backend,
 * - loading and error flags,
 * - and the async action that actually fetches chart data.
 *
 * Keeping this in a store (instead of local component state) makes it:
 * - Easier to share between views/components.
 * - Easier to test and reason about, since all I/O logic is centralized.
 */
const store = useChartStore()

/**
 * Extract reactive references from the store.
 *
 * @constant
 * @type {{ chart: import('vue').Ref<any>, isLoading: import('vue').Ref<boolean>, error: import('vue').Ref<string|null>, params: import('vue').Ref<any> }}
 *
 * Rationale:
 * - `storeToRefs` preserves reactivity when destructuring Pinia stores.
 * - Components can read these refs directly inside the template and computed properties.
 */
const { chart, isLoading, error, params } = storeToRefs(store)

/**
 * Additional Plotly configuration (UI tuning only).
 *
 * @constant
 * @type {import('vue').ComputedRef<object>}
 *
 * Design goals:
 * - Keep Plotly-specific switches in one place, so they can evolve independently.
 * - Expose only presentation concerns (e.g., responsiveness, toolbar behavior),
 *   never business rules or domain-specific logic.
 */
const plotConfig = computed(() => ({
  responsive: true,
  displaylogo: false,
  // Here you can fine-tune Plotly interactions (mode bar, zoom behavior, locale, etc.).
}))

/**
 * Whether there is a "type" parameter that can be used to request a chart.
 *
 * @constant
 * @type {import('vue').ComputedRef<boolean>}
 *
 * Explanation:
 * - The `params` object is owned by the Pinia store and usually mirrors route/query params.
 * - `type` acts as a high-level discriminator of which chart the backend should build.
 * - Trimming the string avoids situations where whitespace is considered a valid value.
 */
const hasTicker = computed(() => !!(params.value?.type || '').trim())

/**
 * Lifecycle hook: called once when the component is mounted in the DOM.
 *
 * Behavior:
 * 1. Checks if we already have a valid "type" (hasTicker).
 * 2. Checks if no chart has been loaded yet.
 * 3. If both conditions hold, it triggers an initial chart load via the store.
 *
 * Why this guard logic matters:
 * - Prevents unnecessary API calls when the user has no selection yet.
 * - Avoids re-fetching when the chart is already in memory (e.g., user navigates within the page).
 * - Keeps the component idempotent: mounting the view multiple times does not spam the backend.
 *
 * Note:
 * - `store.loadChart()` encapsulates all I/O; this component only orchestrates when to call it.
 */
onMounted(async () => {
  // Only load if there is a defined type and the chart state is still empty.
  if (hasTicker.value && !chart.value) {
    await store.loadChart()
  }
})
</script>

<style scoped>
/* Root container: vertical layout with spacing and padding for comfortable reading */
.chart-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

/* Header area: isolated block so it can evolve with additional controls later (filters, breadcrumbs, etc.) */
.chart-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Chart container: ensures minimum height so loading and empty states do not collapse the layout */
.chart-container {
  min-height: 300px;
}

/* Feedback areas: reused styles for loading and error banners */
.chart-loading,
.chart-error {
  padding: 0.5rem;
}
</style>
