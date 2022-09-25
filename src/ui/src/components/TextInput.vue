<script setup lang="ts">
const emit = defineEmits<{
  (e: "change", value: string): void
  (e: "blur", value: Event): void
}>()
defineProps<{
  label?: string
  name?: string
  type?: "text" | "email" | "password"
  value?: string
  lines?: number
  help?: string
  error?: string
  success?: string
}>()
</script>

<template>
  <div class="form-control px-1 py-2">
    <label v-if="label" class="block pb-1 pl-1 text-xs font-semibold tracking-wide text-gray-600 dark:text-gray-100">
      <span class="label-text">{{ label }}</span>
    </label>
    <template v-if="lines && lines > 1">
      <textarea
        v-bind="$attrs"
        :id="name"
        :value="value"
        class="block w-full rounded-lg border-gray-300 p-4 shadow-sm focus:border-info-300 focus:ring-info-300 dark:border-gray-700 sm:text-sm"
        :class="[error ? 'border-error-100 dark:border-error-500' : '', success ? 'border-success-300' : '']"
        :type="type"
        :rows="lines"
        :aria-invalid="error == null ? undefined : true"
        @input="emit('change', ($event?.target as HTMLInputElement)?.value)"
        @blur="emit('blur', $event)"
      />
    </template>
    <template v-else>
      <input
        v-bind="$attrs"
        :id="name"
        :value="value"
        class="block w-full rounded-lg border-gray-300 p-4 shadow-sm focus:border-info-300 focus:ring-info-300 dark:border-gray-700 sm:text-sm"
        :class="[error ? 'border-error-100 dark:border-error-500' : '', success ? 'border-success-300' : '']"
        :type="type"
        :aria-invalid="error == null ? undefined : true"
        @input="emit('change', ($event?.target as HTMLInputElement)?.value)"
        @blur="emit('blur', $event)"
      />
    </template>

    <label v-if="error">
      <span class="h-6 pl-1 text-xs text-gray-800 dark:text-gray-200">
        {{ error }}
      </span>
    </label>
    <label v-else-if="success">
      <span class="h-6 pl-1 text-xs text-success-500">
        {{ success }}
      </span>
    </label>
    <label v-else-if="help">
      <span class="h-6 pl-1 text-xs text-gray-800 dark:text-gray-200">{{ help }}</span>
    </label>
    <label v-else>
      <span class="h-6 pl-1 text-xs text-gray-500">&zwnj;</span>
    </label>
  </div>
</template>
