<template>
  <TransitionRoot appear :show="isShowing">
    <toast-notification />
    <router-view v-slot="{ Component, route }">
      <component :is="Component" :key="route.path" />
    </router-view>
  </TransitionRoot>
</template>
<script setup lang="ts">
import { onMounted, ref } from "vue"
import { TransitionRoot } from "@headlessui/vue"
import ToastNotification from "@/components/ToastNotification.vue"

const isShowing = ref(false)
onMounted(() => {
  isShowing.value = true
})
</script>
