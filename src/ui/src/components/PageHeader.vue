<script setup lang="ts">
import Breadcrumbs from "@/components/Breadcrumbs.vue"
import EnvironmentDropdown from "@/components/CurrentEnvironmentDropdown.vue"
import { FunctionalComponent } from "vue"
const props = defineProps<{
  breadcrumbs?: { id: number; to: string; label: string; icon?: FunctionalComponent; current?: boolean }[]
}>()
</script>
<template>
  <div class="mb-6 flex">
    <div class="min-w-max flex-shrink-0 sm:w-1/2">
      <breadcrumbs :breadcrumbs="props.breadcrumbs" />
      <h1 class="pt-0.5 text-xl font-bold tracking-wide text-gray-800 dark:text-gray-50"><slot></slot></h1>
    </div>
    <div class="invisible flex justify-end sm:visible sm:w-1/2">
      <environment-dropdown />
    </div>
  </div>
</template>
