<template>
  <button
    :type="props.type"
    :class="[
      props.size === 'xs' ? 'mt-2 px-4 py-2 text-xs' : '',
      props.size === 'sm' ? 'mt-2 px-4 py-2 text-sm' : '',
      props.size === 'md' ? 'text-md mt-2 px-4 py-2' : '',
      props.size === 'lg' ? 'text-md mt-2 px-4 py-4' : '',
      props.size === 'xl' ? 'mt-4 px-6 py-6 text-lg' : '',
    ]"
    class="hover:bg-hover-focus items-center rounded-lg border border-transparent bg-secondary font-semibold uppercase tracking-wider text-white shadow-sm active:animate-button-pop"
  >
    <slot></slot>
  </button>
</template>
<script setup lang="ts">
interface Props {
  type: "submit" | "button" | "reset" | undefined
  size: "xs" | "sm" | "md" | "lg" | "xl" | undefined
}

const props = withDefaults(defineProps<Props>(), {
  type: "submit",
  size: "md",
})
</script>
