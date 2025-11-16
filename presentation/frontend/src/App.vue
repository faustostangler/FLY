<!-- src/App.vue -->
<template>
  <!-- Navigation container -->
  <div class="component-box">
    <!-- Basic links to routes -->
    <a href="http://localhost:5173/">Home</a> |
    <a href="http://localhost:5173/charts">Chart</a> |
  </div>

  <div>
    <!-- App header -->
    <header>
      <h1>FLY Project</h1>
    </header>

    <!-- Route outlet where pages (views/) are rendered -->
    <router-view />

    <!-- Footer note -->
    <p>
      (c) Crafted in the Pampas and powered by yerba mate: an authentic gaucho tech.
    </p>
  </div>
</template>

<script setup>
/**
 * App.vue
 *
 * Root component of the Vue application.
 * It hosts:
 *   1. Global navigation links.
 *   2. A shared header.
 *   3. <router-view> where each routable view is rendered.
 *
 * This file usually stays minimal because:
 *   - It should not contain business logic.
 *   - It only coordinates global layout.
 *   - Stores, components, and routes are orchestrated elsewhere.
 */
</script>

<style>
/* Global body resets */
body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Header styling */
header {
  padding: 1rem;
  border-bottom: 1px solid #ccc;
}

/* Generic page wrapper for spacing and layout */
.page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 40px;
  background-color: rgba(45, 180, 169, 0.423);
}

/* Box around navigation links */
.component-box {
  border: 10px solid rgba(0, 217, 255, 0.25);
  border-radius: 12px;
  background-color: rgb(255, 255, 255);
  padding: 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}
</style>
