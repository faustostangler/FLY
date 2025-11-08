<template>
  <section class="company-search">
    <header class="company-search__header">
      <h2>Construtor de filtros</h2>
      <div class="company-search__actions">
        <button type="button" class="ghost" @click="clearFilters">
          Limpar filtros
        </button>
        <button type="button" @click="reload">Buscar</button>
      </div>
    </header>

    <section class="company-search__facets" aria-labelledby="filters-heading">
      <h2 id="filters-heading">Filtros</h2>

      <CompanyFacet
        v-for="facet in facetConfigs"
        :key="facet.field"
        :field="facet.field"
        :label="facet.label"
        :options="facetOptions(facet.field)"
        :logical="clauseLogical(facet.field)"
        :values="clauseValues(facet.field)"
        :multiple="facet.multiple !== false"
        @change="onFacetChange"
      />
    </section>

    <div class="company-search__query">
      <label for="queryText">Consulta estruturada</label>
      <textarea
        id="queryText"
        v-model="queryTextModel"
        rows="2"
        placeholder="AND sector IN (Energia, Financeiro)"
      ></textarea>
      <div class="company-search__query-actions">
        <button type="button" @click="applyQuery">Aplicar consulta</button>
        <span v-if="parseError" class="company-search__error">
          {{ parseError }}
        </span>
      </div>
    </div>

    <div class="company-search__results">
      <header>
        <h3>Resultados ({{ total }})</h3>
        <span v-if="isLoading" class="company-search__status">Carregando...</span>
        <span v-else-if="error" class="company-search__error">{{ error }}</span>
      </header>

      <CompanyResultSelect
        v-model="selectedItemsModel"
        :companies="companies"
        :disabled="isLoading || !companies.length"
      />

      <p v-if="!companies.length && !isLoading" class="muted">
        Nenhuma companhia encontrada com os filtros atuais.
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import CompanyFacet from './CompanyFacet.vue'
import CompanyResultSelect from './CompanyResultSelect.vue'
import { useCompanyStore } from '../store/companyStore'

const store = useCompanyStore()

const facetConfigs = computed(() => store.facetConfigs || [])
const companies = computed(() => store.companies || [])
const total = computed(() => store.total ?? companies.value.length)
const error = computed(() => store.error)
const isLoading = computed(() => store.isLoading)
const parseError = computed(() => store.parseError)

const queryTextModel = computed({
  get: () => store.queryText,
  set: (value) => store.updateQueryText(value),
})

const selectedItemsModel = computed({
  get: () => store.selectedItems,
  set: (value) => store.updateSelectedItems(value),
})

const facetOptions = (field) => store.facetOptions(field)
const clauseValues = (field) => store.clauseValues(field)
const clauseLogical = (field) => store.clauseLogical(field)

const reload = () => store.reload()
const clearFilters = () => store.clearFilters()
const applyQuery = () => store.applyQuery()

const onFacetChange = (payload) => {
  store.updateFacet(payload)
}
</script>

<style scoped>
.company-search {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.company-search__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.company-search__actions {
  display: flex;
  gap: 0.5rem;
}

.company-search__facets {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.company-search__query {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.company-search__query textarea {
  width: 100%;
  resize: vertical;
}

.company-search__query-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.company-search__results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.company-search__error {
  color: #d93025;
}

.company-search__status {
  color: #666;
}

.muted {
  color: #666;
}

button {
  padding: 0.5rem 1rem;
}

button.ghost {
  background: transparent;
  border: 1px solid currentColor;
}
</style>
