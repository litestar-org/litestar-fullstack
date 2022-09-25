<template>
  <sidebar-layout :breadcrumbs="breadcrumbs">
    <template #header>User Profile</template>
    <template #main>
      <div class="py-6">
        <edit-profile-form />
        <edit-password-form />
      </div>
    </template>
  </sidebar-layout>
</template>
<script setup lang="ts">
import SidebarLayout from "@/layouts/SidebarLayout.vue"
import EditProfileForm from "@/pages/profile/_partials/EditProfileForm.vue"
import EditPasswordForm from "@/pages/profile/_partials/EditPasswordForm.vue"

const breadcrumbs = [
  { id: 1, to: "/", label: "Home" },
  { id: 2, to: "/profile", label: "Profile", current: true },
]
</script>
