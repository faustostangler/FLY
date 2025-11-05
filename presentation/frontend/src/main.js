import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { VuePlotly } from 'vue3-plotly'   // <- AQUI: import nomeado

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.component('VuePlotly', VuePlotly)    // <- registra o componente
app.mount('#app')
