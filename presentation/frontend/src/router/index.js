// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ChartView from '../views/ChartView.vue'
import AccountChartsView from '../views/AccountChartsView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
  },
  {
    path: '/charts',
    name: 'charts',
    component: ChartView,
  },
  {
    path: '/charts/accounts',
    // Keep this name in sync with views that navigate to the account charts page.
    name: 'account-charts',
    component: AccountChartsView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
