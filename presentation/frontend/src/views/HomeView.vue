<template>
  <!--
    High-level layout:
    1) Search area for building the company query
    2) Summary of selected company pairs and CTA to view charts
    3) Charts results area that reacts to the current selection
  -->
  <main class="home">
    <!--
      Company search and filtering section.
      This section is responsible for letting the user discover and select companies.
      The internal logic of <CompanySearchBuilder> manages the filter form and search results.
    -->
    <section id=CompanySearchBuilder class="home__search">
      <CompanySearchBuilder />
    </section>

    <!--
      Selection summary and "visualize charts" trigger.
      This section mirrors the current selection of company pairs and exposes a clear CTA
      for the user to request chart rendering.
    -->
    <section id="CompanySelectionSummary" class="home__charts">
        <!-- Title for the dashboard, bound to a reactive ref in the script block -->
        <h2>{{ title }}</h2>

        <!--
          <CompanySelectionSummary> responsibilities:
          - Display the current selected company pairs (read-only)
          - Emit "visualizar-graficos" when the user decides to see charts

          The parent (this view) handles the event and coordinates the chart store update.
        -->
        <CompanySelectionSummary
          :selected-pairs="selectedPairs"
          @visualizar-graficos="onVisualizarGraficos"
        />
    </section>

    <!--
      Charts results container.
      - If there are selected pairs, delegate rendering to <CompanyChartsView>.
      - Otherwise, show an instructional empty state to guide the user.
    -->
    <section id="CompanyChartsView" class="home__charts-results">
      <h2>Resultados</h2>

        <!--
          Charts area:
          - guarded by v-if="selectedPairs.length"
          - aria-labelledby links the region to the heading for accessibility tools
        -->
        <div v-if="selectedPairs.length" aria-labelledby="chart-results-heading">
            <CompanyChartsView />
        </div>

        <!--
          Empty-state message when there are no selected companies.
          This prevents confusing blank space and explicitly tells the user what to do next.
        -->
        <div v-else class="home__charts-empty">
          Selecione uma ou mais companhias e clique em “Visualizar Gráficos”.
        </div>
    </section>
  </main>
</template>

<script setup>
/**
 * Home view:
 * - Acts as a composition root: orchestrates stores, child components and user flows.
 * - Does not contain business rules; instead, it coordinates state and events.
 * - Delegates domain logic to Pinia stores and reusable components.
 */

import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'

/**
 * UI components:
 * - CompanySearchBuilder: handles search filters and company discovery.
 * - CompanySelectionSummary: shows current selection and exposes "visualize charts" CTA.
 * - CompanyChartsView: renders charts based on state managed by the charts store.
 */
import CompanySearchBuilder from '../components/CompanySearchBuilder.vue'
import CompanySelectionSummary from '../components/CompanySelectionSummary.vue'
import CompanyChartsView from '../components/CompanyChartsView.vue'

/**
 * Pinia stores:
 * - useCompanyStore: owns company data, filters and selected pairs.
 * - useAccountChartsStore: owns chart parameters and chart data for the dashboard.
 */
import { useCompanyStore } from '../store/companyStore'
import { useAccountChartsStore } from '../store/companyChartsStore'

/**
 * Dashboard title as a reactive ref.
 * Keeping it reactive allows dynamic renaming in the future (e.g., i18n or user preferences)
 * without changing the template contract.
 * @type {import('vue').Ref<string>}
 */
const title = ref('Dashboard de Indicadores')

/**
 * Step 1: Initialize stores.
 * The view depends on these stores as its single source of truth for:
 * - selected company pairs
 * - chart selection and loading lifecycle
 */
const companyStore = useCompanyStore()
const chartsStore = useAccountChartsStore()

/**
 * Step 2: Extract a reactive reference to "selectedPairs" from the company store.
 * storeToRefs:
 * - Preserves reactivity when de-structuring store properties.
 * - Avoids losing reactivity that would occur with plain ES destructuring.
 */
const { selectedPairs: selectedPairsRef } = storeToRefs(companyStore)

/**
 * Step 3: Normalize "selectedPairs" to always be an array.
 *
 * Motivation:
 * - The template and downstream logic assume "selectedPairs" is an array.
 * - Defensive programming: if the store ever returns null/undefined/non-array,
 *   we gracefully downgrade to an empty list instead of crashing bindings.
 *
 * @type {import('vue').ComputedRef<Array<unknown>>}
 */
const selectedPairs = computed(() => {
  const pairs = selectedPairsRef.value
  // Guard against unexpected types and default to an empty array for robustness.
  return Array.isArray(pairs) ? pairs : []
})

/**
 * Step 4: Handle "Visualizar Gráficos" action from the summary component.
 *
 * Responsibilities:
 * - Push the current company selection into the charts store.
 * - Set the accounts that should be visualized (currently a fixed initial choice).
 * - Trigger asynchronous loading of chart data from the backend.
 *
 * Design notes:
 * - This function is a coordination layer only; no business rules here.
 * - Business rules about what "setCompanies", "setSelectedAccounts" and "loadCharts"
 *   actually mean live in the charts store and use cases behind it.
 *
 * @returns {void}
 */
const onVisualizarGraficos = () => {
  // 1) Inform the charts store which companies should be used as chart inputs.
  chartsStore.setCompanies(selectedPairs.value)

  // 2) Define which accounts/indicators should be visualized.
  //    This initial value can later be driven by user input or configuration.
  chartsStore.setSelectedAccounts(['02.03'])

  // 3) Trigger the chart loading process (likely async I/O to the backend).
  //    The store is responsible for managing isLoading, error states and data.
  chartsStore.loadCharts()
}
</script>

<style scoped>
/*
  Layout:
  - Column-based layout for a vertical dashboard.
  - Gap provides consistent spacing between core sections.
*/
.home {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 1rem;
}

/*
  Charts summary section:
  - Structured as a vertical stack
  - Light blue background hints at "information" and separates the block visually.
*/
.home__charts {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  background-color: #a3c6f1;
  border-radius: 50px;
}

/*
  Charts results section:
  - Similar vertical layout for consistency with the summary area.
  - Different color helps users visually distinguish "inputs" vs "results".
*/
.home__charts-results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background-color: #d2f7c3;
  border-radius: 50px;
}

/*
  Search section:
  - Full-width block for filters and search controls.
  - Neutral background to keep focus on form controls inside <CompanySearchBuilder>.
*/
.home__search {
  max-width: 100%;
  background-color: #dde1e6;
  border-radius: 50px;
}

/*
  Empty state styling:
  - Muted color communicates secondary, informational text.
  - Used when there are no selected companies to generate charts.
*/
.home__charts-empty {
  color: #64748b;
}
</style>
