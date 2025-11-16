// src/router/index.js

/**
 * Router configuration for the web presentation layer.
 * Uses Vue Router with HTML5 history mode.
 *
 * Architectural note:
 * Views act as composition roots: they orchestrate stores,
 * components, and route parameters. They are not reusable
 * components. Each route maps directly to one high-level view.
 */

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ChartView from '../views/ChartView.vue'

/**
 * Route definitions.
 *
 * Step-wise notes:
 * 1. Each route binds a URL path to a view component.
 * 2. Names provide stable identifiers for navigation.
 * 3. Views are high-level containers, not UI components.
 */
const routes = [
  {
    // Step 1: Root path → main landing view
    path: '/',
    name: 'home',
    component: HomeView,
  },
  {
    // Step 2: Charts path → dedicated charts page/view
    // This view coordinates Pinia state, components, and API calls.
    path: '/charts',
    name: 'charts',
    component: ChartView,
  },
]

/**
 * Router instance.
 *
 * Step-wise notes:
 * 1. createWebHistory() uses clean URLs (no hash).
 * 2. attach all registered routes.
 * 3. export a singleton router for the entire application.
 */
const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
