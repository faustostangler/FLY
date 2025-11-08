<template>
  <div class="plotly-viewer">
    <div class="plotly-viewer__placeholder">Gráfico será exibido aqui.</div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.plotly-viewer {
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.plotly-viewer__placeholder {
  color: #888;
}
</style>
