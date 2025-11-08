<template>
  <div id="app">
    <header class="app-header">
      <h1>FLY Project</h1>
    </header>
    <HomeView />
  </div>
</template>

<script setup>
import HomeView from './views/HomeView.vue'
</script>

<style scoped>
#app {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI',
    sans-serif;
  line-height: 1.5;
  color: #111;
}

.app-header {
  margin-bottom: 2rem;
}
</style>
