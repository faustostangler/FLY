// src/main.js

/**
 * @file Main entrypoint of the frontend application.
 * Initializes Vue, registers global providers (Pinia, Router),
 * attaches global components, and mounts the root App component.
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { VuePlotly } from 'vue3-plotly'

/**
 * Step 1 — Create the root Vue application instance.
 * This instance becomes the top-level orchestrator of the UI.
 */
const app = createApp(App)

/**
 * Step 2 — Register global state management (Pinia).
 * Pinia provides a central, reactive, typesafe store system.
 * Every component can access stores without prop-drilling.
 */
app.use(createPinia())

/**
 * Step 3 — Register the router.
 * The router controls navigation and URL-driven view rendering.
 * Views under /src/views/ are directly mounted through this router.
 */
app.use(router)

/**
 * Step 4 — Register global Plotly component.
 * Allows <VuePlotly> to be used in any component without local import.
 * Useful for shared visualization elements.
 */
app.component('VuePlotly', VuePlotly)

/**
 * Step 5 — Mount the application.
 * Vue transforms <App/> into a live DOM tree inside #app.
 * This finalizes initialization and renders the UI for the user.
 */
app.mount('#app')
