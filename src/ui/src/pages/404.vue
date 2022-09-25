<script setup lang="ts">
import { useHead } from "@vueuse/head"
import CenteredLayout from "@/layouts/CenteredLayout.vue"
useHead({
  title: "404. Not Found",
})
</script>

<template>
  <centered-layout>
    <div class="flex min-h-full flex-col pt-16 pb-12">
      <main class="mx-auto flex w-full flex-grow flex-col justify-center px-4 sm:px-6 lg:px-8">
        <div class="flex flex-shrink-0 justify-center">
          <a href="/" class="inline-flex">
            <application-logo class="h-56 w-full flex-row"></application-logo>
          </a>
        </div>
        <div class="pt-8 pb-16">
          <div class="text-center">
            <p class="text-sm font-semibold uppercase tracking-wide text-secondary">404 error</p>
            <h1 class="mt-2 text-4xl font-extrabold tracking-tight text-base-content sm:text-5xl">Page not found.</h1>
            <p class="mt-2 text-base text-neutral">Sorry, we couldn’t find the page you’re looking for.</p>
            <div class="mt-6">
              <router-link to="/" class="text-base font-medium text-secondary hover:text-secondary-focus">
                Go back home
                <span aria-hidden="true">&rarr;</span>
              </router-link>
            </div>
          </div>
        </div>
      </main>
      <footer class="mx-auto w-full flex-shrink-0 px-4 sm:px-6 lg:px-8">
        <nav class="flex justify-center space-x-4">
          <a href="https://docs.gluent.com" class="text-sm font-medium text-neutral hover:text-neutral-focus">
            Contact Support
          </a>
        </nav>
      </footer>
    </div>
  </centered-layout>
</template>
