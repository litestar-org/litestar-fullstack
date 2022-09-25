<template>
  <div class="">
    <div class="flex flex-wrap items-center justify-between sm:flex-nowrap">
      <div class="mt-4">
        <h3 class="text-lg font-medium leading-6 text-base-content">
          <slot name="title"></slot>
        </h3>

        <p class="mt-1 text-sm text-base-content text-opacity-75">
          <slot name="description"></slot>
        </p>
      </div>

      <div class="mt-4 ml-4 flex-shrink-0">
        <slot name="aside"></slot>
      </div>
    </div>
  </div>
</template>
