import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import VuePlotly from 'vue-plotly'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.component('VuePlotly', VuePlotly)
app.mount('#app')
