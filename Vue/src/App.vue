<script setup>
import {ref} from 'vue'
import Cats from './components/Cats.vue'
import Toast from './components/Toast.vue'

const cat = ref('')
</script>

<template>
  <main>
    <Cats v-model="cat" v-slot="{ getCats }">
      <button @click="getCats">Gimme a cat</button>
      <div/>
      <img :src="cat"/>
    </Cats>
  </main>
  <footer>
    <Toast/>
  </footer>
</template>
