<template>
  <section class="chart-selector">
    <label for="chartType">Tipo de gráfico</label>
    <input
      id="chartType"
      v-model="localType"
      type="text"
      @keyup.enter="apply"
      aria-label="Tipo de gráfico"
    />

    <button type="button" @click="apply">
      Carregar gráfico
    </button>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChartStore } from '../store/chartStore'

const store = useChartStore()
const route = useRoute()
const router = useRouter()

const localType = ref(route.query.type || store.params.type)

// sincroniza rota -> campo
watch(
  () => route.query.type,
  (value) => {
    if (value && value !== localType.value) {
      localType.value = value
      store.updateParams({ type: value })
    }
  }
)

async function apply() {
  const type = localType.value || 'test'

  // atualiza query string
  router.replace({ query: { ...route.query, type } })

  await store.updateParams({ type })
}
</script>
