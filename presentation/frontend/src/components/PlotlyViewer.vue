<template>
  <section class="plotly-viewer" aria-labelledby="plotly-viewer-heading">
    <h3 id="plotly-viewer-heading">{{ props.title }}</h3>
    <div class="plotly-viewer__content">
      <div class="plotly-viewer__placeholder">Gráfico será exibido aqui.</div>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  title: {
    type: String,
    default: 'Preço',
  },
})
</script>

<style scoped>
.plotly-viewer {
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.plotly-viewer__content {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.plotly-viewer__placeholder {
  color: #888;
}
</style>
