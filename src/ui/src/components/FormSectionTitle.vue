<template>
  <div class="flex justify-between md:col-span-1">
    <div class="pt-4 pb-2">
      <h3 class="text-lg font-medium leading-6 text-base-content">
        <slot name="title"></slot>
      </h3>

      <p class="mt-1 text-sm text-base-content text-opacity-75">
        <slot name="description"></slot>
      </p>
    </div>

    <div class="px-4 sm:px-0">
      <slot name="aside"></slot>
    </div>
  </div>
</template>
