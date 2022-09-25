<template>
  <teleport to="body">
    <transition leave-active-class="duration-200">
      <div v-show="show" class="fixed inset-0 z-50 overflow-y-auto px-4 py-6 sm:px-0" scroll-region>
        <transition
          enter-active-class="duration-300 ease-out"
          enter-from-class="opacity-0"
          enter-to-class="opacity-100"
          leave-active-class="duration-200 ease-in"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div v-show="show" class="fixed inset-0 transform transition-all" @click="close">
            <div class="absolute inset-0 bg-base-300 opacity-75"></div>
          </div>
        </transition>

        <transition
          enter-active-class="duration-300 ease-out"
          enter-from-class="translate-y-4 opacity-0 sm:translate-y-0 sm:scale-95"
          enter-to-class="translate-y-0 opacity-100 sm:scale-100"
          leave-active-class="duration-200 ease-in"
          leave-from-class="translate-y-0 opacity-100 sm:scale-100"
          leave-to-class="translate-y-4 opacity-0 sm:translate-y-0 sm:scale-95"
        >
          <div
            v-show="show"
            class="mb-6bg-base-100 transform overflow-hidden rounded-lg shadow transition-all dark:bg-base-100-dark sm:mx-auto sm:w-full"
            :class="maxWidthClass"
          >
            <slot v-if="show"></slot>
          </div>
        </transition>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { watch, onMounted, onUnmounted, computed } from "vue"

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
const emit = defineEmits(["close"])

const close = () => {
  if (props.closeable) {
    emit("close")
  }
}

const closeOnEscape = (e: { key: string }) => {
  if (e.key === "Escape" && props.show) {
    close()
  }
}

onMounted(() => document.addEventListener("keydown", closeOnEscape))
onUnmounted(() => {
  document.removeEventListener("keydown", closeOnEscape)
  document.body.style.overflow = ""
})
const maxWidthClass = computed(() => {
  return {
    sm: "sm:max-w-sm",
    md: "sm:max-w-md",
    lg: "sm:max-w-lg",
    xl: "sm:max-w-xl",
    "2xl": "sm:max-w-2xl",
  }[props.maxWidth]
})

watch(props.show.valueOf, () => (show: boolean) => {
  if (show) {
    document.body.style.overflow = "hidden"
  } else {
    document.body.style.overflow = ""
  }
})
</script>
