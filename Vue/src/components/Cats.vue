<script>
import {pushMessage} from '../composables/toast.js'
export default {
  name: 'Cats',
  props: {
    modelValue: {
      type: String,
      required: true,
    },
  },
  methods: {
    async getCats() {
      pushMessage('Hello Cat')
      const response = await fetch('https://cataas.com/cat')
      const data = await response.blob()
      const blobUrl = URL.createObjectURL(data)
      this.$emit('update:modelValue', blobUrl)
    },
  },
  render() {
    return this.$slots.default({
      getCats: this.getCats,
    })
  },
}
</script>