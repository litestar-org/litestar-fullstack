<template>
  <centered-layout>
    <div class="w-full max-w-md">
      <application-logo class="h-32 w-full flex-row pb-4"></application-logo>

      <h2 class="text-content-base mb-12 text-center text-3xl font-extrabold text-gray-800 dark:text-gray-50">
        Enterprise Console
      </h2>
      <FlashMessage v-if="flashMessage" :flash-message="flashMessage" />
      <form @submit="onSubmit">
        <text-input
          name="username"
          type="email"
          label="User"
          placeholder="Username or Email"
          autocomplete="off"
          :value="form.field('username').value"
          :error="form.field('username').error"
          @change="form.field('username').onChange"
          @blur="form.field('username').onBlur"
        />
        <text-input
          name="password"
          type="password"
          label="Password"
          placeholder="Current password"
          autocomplete="off"
          :value="form.field('password').value"
          :error="form.field('password').error"
          @change="form.field('password').onChange"
          @blur="form.field('password').onBlur"
        />

        <div class="mt-6 flex items-center justify-between text-sm text-gray-800 dark:text-gray-100">
          <router-link to="/register" class="link link-hover">Need an account?</router-link>
          <router-link to="/reset-password" class="link link-hover">Forgot your password?</router-link>
        </div>

        <div>
          <primary-button type="submit" :disabled="isSubmitting" class="w-full" size="lg">Sign in</primary-button>
        </div>
      </form>
    </div>
  </centered-layout>
</template>

<script setup lang="ts">
import { ErrorMessage } from "@/api/client"
import { FlashMessageNotification } from "@/api/types"
import FlashMessage from "@/components/FlashMessage.vue"
import PrimaryButton from "@/components/PrimaryButton.vue"
import TextInput from "@/components/TextInput.vue"
import CenteredLayout from "@/layouts/CenteredLayout.vue"
import { useForm } from "@/composables/useForm"
import { useAuth } from "@/composables/useAuth"
import { notify } from "notiwind"
import { ref } from "vue"
import * as z from "zod"
const auth = useAuth()

const formSchema = z.object({
  username: z
    .string({
      required_error: "Username is required",
    })
    .email({ message: "A valid username is required." }),
  password: z
    .string({ required_error: "Password is required" })
    .min(6, { message: "Password must be greater than 6 characters" }),
})
const form = useForm(formSchema)
let flashMessage = ref<FlashMessageNotification>()

const { handleSubmit, isSubmitting } = form
const onSubmit = handleSubmit(async (values) => {
  const result = await auth.login(values)
  if ((result as ErrorMessage).error) {
    form.setError(result as ErrorMessage)
  } else {
    notify(
      {
        type: "info",
        group: "alerts",
        title: "Logged In",
        text: "You have successfully logged in.",
      },
      3000
    )
  }
})
</script>
