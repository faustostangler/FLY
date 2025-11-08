<template>
  <section aria-labelledby="company-heading">
    <h3 id="company-heading">Companhia</h3>

    <p v-if="!selectedSummaries.length" class="muted">
      Use o menu de resultados para escolher uma ou mais combinações de companhia e ticker.
    </p>

    <ul v-else class="company-search__selection">
      <li v-for="item in selectedSummaries" :key="item.key">
        <h4>{{ item.companyName }}</h4>
        <div class="company-search__tags">
          <span class="tag">{{ item.ticker }}</span>
          <span v-if="item.market" class="tag tag--outline">
            {{ item.market }}
          </span>
        </div>
        <p v-if="item.tradingName" class="muted">
          {{ item.tradingName }}
        </p>
        <p class="muted">
          <span v-if="item.sector">Setor: {{ item.sector }} · </span>
          <span v-if="item.subsector">Subsetor: {{ item.subsector }} · </span>
          <span v-if="item.segment">Segmento: {{ item.segment }}</span>
        </p>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useCompanyStore } from '../store/companyStore'

const store = useCompanyStore()

const selectedSummaries = computed(() => store.selectedSummaries || [])
</script>

<style scoped>
.company-search__selection {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.company-search__tags {
  display: flex;
  gap: 0.5rem;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  background: #f0f0f0;
  font-size: 0.875rem;
}

.tag--outline {
  border: 1px solid currentColor;
  background: transparent;
}

.muted {
  color: #666;
}
</style>
