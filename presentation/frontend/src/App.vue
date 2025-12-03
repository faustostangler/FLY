<!-- src/App.vue -->
<template>
  <section id="top-nav" class="component-box">
    <a href="http://localhost:5173/">Home</a> |
    <!-- <a href="http://localhost:5173/charts">Chart</a> |
    <a href="http://localhost:5173/charts/accounts">Contas</a> -->
  </section>
  <section id="header">
    <h1>FLY Project</h1>
  </section>
  <section id="body">
    <router-view />
  </section>
  <section id="footer" class="component-box">
    <p>
      (c) Crafted in the Pampas and powered by yerba mate: an authentic gaucho tech.
    </p>
  </section>
</template>

<script setup>
</script>

<style>
body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

header {
  padding: 1rem;
  border-bottom: 1px solid #ccc;
}

.page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 40px;
  background-color: rgba(45, 180, 169, 0.423);
}

.component-box {
  border: 10px solid rgba(0, 217, 255, 0.25);
  border-radius: 12px;
  background-color: rgb(255, 255, 255);
  padding: 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}
</style>
