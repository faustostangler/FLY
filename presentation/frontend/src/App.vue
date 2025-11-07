<!-- src/App.vue -->
<template>
  <div class=""component-box>
    <a href="http://localhost:5173/">Home</a> |
    <a href="http://localhost:5173/charts">Chart</a>
  </div>
  <div>
    <header>
      <h1>FLY Project</h1>
    </header>
    <!-- aqui as views vão ser renderizadas conforme a rota -->
    <router-view />
    <p>(c) Crafted in the Pampas and powered by yerba mate: an authentic gaucho tech.</p>
  </div>
</template>

<script setup>
// por enquanto, nada aqui
</script>

<style>
/* estilos simples, opcionais */
body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
header {
  padding: 1rem;
  border-bottom: 1px solid #ccc;
}
<style>
.page {
  display: flex;
  flex-direction: column;     /* um box embaixo do outro */
  gap: 20px;                  /* espaçamento entre boxes */
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
