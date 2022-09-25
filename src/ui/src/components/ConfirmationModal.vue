<script setup lang="ts">
import Modal from "@/components/Modal.vue"
const emit = defineEmits(["close"])

const close = () => {
  if (props.closeable) {
    emit("close")
  }
}

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  maxWidth: {
    type: String,
    default: "2xl",
  },
  closeable: {
    type: Boolean,
    default: true,
  },
})
</script>
<template>
  <modal :show="props.show" :max-width="props.maxWidth" :closeable="props.closeable" @close="close">
    <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
      <div class="sm:flex sm:items-start">
        <div
          class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10"
        >
          <svg class="h-6 w-6 text-red-600" stroke="currentColor" fill="none" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
          <h3 class="text-lg">
            <slot name="title"></slot>
          </h3>

          <div class="mt-2">
            <slot name="content"></slot>
          </div>
        </div>
      </div>
    </div>

    <div class="text-right bg-base-200 px-6 py-4 dark:bg-base-200-dark">
      <slot name="footer"></slot>
    </div>
  </modal>
</template>
