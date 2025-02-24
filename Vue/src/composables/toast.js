import {ref} from 'vue'

const message = ref('Hello Cat')
const show = ref(false)

const pushMessage = m => {
  if (show.value === true) {
    return
  }
  
  message.value = m
  show.value = true
  setTimeout(() => { show.value = false}, 3000)
}

export {
  message,
  show,
  pushMessage,
}