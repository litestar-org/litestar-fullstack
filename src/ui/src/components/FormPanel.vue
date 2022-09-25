<template>
  <div class="rounded-xl border bg-white px-4 py-5 shadow-sm dark:bg-gray-600">
    <div class="md:grid md:grid-cols-3 md:gap-6">
      <div class="md:col-span-1">
        <section-title class="bg-base-100">
          <template #title><slot name="title"></slot></template>
          <template #description><slot name="description"></slot></template>
        </section-title>
      </div>

      <div class="mt-5 md:col-span-2 md:mt-0">
        <form v-bind="$attrs" @submit="onSubmit">
          <div
            class="bg-base-100 py-5 px-4 dark:bg-base-100-dark sm:p-6"
            :class="hasActions ? 'sm:rounded-tl-md sm:rounded-tr-md' : 'sm:rounded-md'"
          >
            <div class="grid grid-cols-6 gap-6">
              <slot name="form"></slot>
            </div>
          </div>

          <div
            v-if="hasActions"
            class="flex items-center justify-end px-4 py-3 text-right sm:rounded-bl-md sm:rounded-br-md sm:px-6"
          >
            <slot name="actions"></slot>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, useSlots } from "vue"
import SectionTitle from "@/components/SectionTitle.vue"

const hasActions = computed(() => {
  return slots.actions
})
const slots = useSlots()

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const onSubmit = async (values: Record<string, any>) => {
  emit("validSubmit", values)
}
const emit = defineEmits(["validSubmit", "invalidSubmit"])
</script>
