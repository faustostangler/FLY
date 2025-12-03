// src/main.js
import { createApp } from 'vue'
import 
App from './App.vue'

import { createPinia } from 'pinia'
import router from './router'
import { VuePlotly } from 'vue3-plotly'

const app = createApp(App)

// registra o gerenciador de estado global
app.use(createPinia())

// registra o roteador
app.use(router)

// Ploply component
app.component('VuePlotly', VuePlotly)


// monta na div com id="app" do index.html
app.mount('#app')
