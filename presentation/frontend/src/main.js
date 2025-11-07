// src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// registra o gerenciador de estado global
app.use(createPinia())

// registra o roteador
app.use(router)

// monta na div com id="app" do index.html
app.mount('#app')
