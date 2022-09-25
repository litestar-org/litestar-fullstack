<template>
  <div class="rounded-md p-4">
    <div class="flex">
      <div class="flex-shrink-0">
        <ExclamationIcon
          v-if="props.flashMessage.messageType === 'warning'"
          class="h-5 w-5 text-warning-400"
          aria-hidden="true"
        />
      </div>
      <div class="ml-3">
        <h3 class="text-sm font-medium text-warning-800">{{ flashMessage.title }}</h3>
        <div class="mt-2 text-sm text-warning-700">
          <p>
            {{ flashMessage.message }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// import { useAppStore } from '@/stores/app'
// import { storeToRefs } from 'pinia'
import { FlashMessageNotification } from "@/api/types"
import { ExclamationIcon } from "@heroicons/vue/outline"
const props = defineProps<{
  flashMessage: FlashMessageNotification
}>()
</script>
