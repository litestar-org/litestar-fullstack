<template>
  <centered-layout>
    <div class="w-full max-w-md">
      <application-logo class="h-32 w-full flex-row pb-4"></application-logo>

      <h2 class="text-content-base mb-8 text-center text-3xl font-extrabold">Enterprise Console</h2>

      <form class="space-y-4" @submit="onSubmit">
        <text-input name="email" type="email" label="User" placeholder="Username or Email" autocomplete="off" />

        <div class="flex items-center justify-between text-sm">
          <router-link to="/register" class="link link-hover">Need an account?</router-link>
          <router-link to="/login" class="link link-hover">Already have an account?</router-link>
        </div>

        <div>
          <PrimaryButton type="submit" :disabled="isSubmitting" class="w-full" size="lg">
            Send Password Reset Instructions
          </PrimaryButton>
        </div>
      </form>
    </div>
  </centered-layout>
</template>

<script setup lang="ts">
import TextInput from "@/components/TextInput.vue"
import { ErrorMessage } from "@/api/client"
import CenteredLayout from "@/layouts/CenteredLayout.vue"
import PrimaryButton from "@/components/PrimaryButton.vue"
import * as z from "zod"
import { useAuth } from "@/composables/useAuth"
import { useForm } from "@/composables/useForm"

const formSchema = z.object({
  email: z
    .string({ required_error: "Username is required to continue" })
    .email({ message: "Please enter a valid email address." }),
})
const auth = useAuth()
const form = useForm(formSchema)

const { handleSubmit, isSubmitting } = form
const onSubmit = handleSubmit(async (values) => {
  const result = await auth.requestPasswordReset(values)
  if ((result as ErrorMessage).error) {
    form.setError(result as ErrorMessage)
  } else {
    console.log(auth.currentUser)
  }
})
</script>
