<template>
  <centered-layout>
    <div class="w-full max-w-md">
      <application-logo class="h-32 w-full flex-row pb-4"></application-logo>

      <h2 class="text-content-base mb-12 text-center text-3xl font-extrabold text-gray-800 dark:text-gray-50">
        Enterprise Console
      </h2>
      <FlashMessage v-if="flashMessage" :flash-message="flashMessage" />

      <form @submit="onSubmit">
        <div class="">
          <text-input name="fullName" type="text" label="Full Name" class="w-full" autocomplete="off"></text-input>
          <text-input name="email" type="email" label="Email" autocomplete="off"></text-input>
        </div>
        <div class="divider divider-horizontal mt-4 mb-4 divide-neutral-600 align-middle"></div>

        <div class="flex">
          <text-input name="password" type="password" label="Password" autocomplete="off" class="w-full" />
          <text-input
            name="passwordConfirm"
            type="password"
            label="Confirm Password"
            autocomplete="off"
            class="w-full"
          />
        </div>
        <div class="mt-6 flex items-center justify-between text-sm text-gray-800 dark:text-gray-100">
          <router-link to="/login" class="link link-hover">Already have an account?</router-link>
        </div>

        <div>
          <PrimaryButton type="submit" size="lg" class="w-full" :disabled="isSubmitting">Sign Up</PrimaryButton>
        </div>
      </form>
    </div>
  </centered-layout>
</template>

<script setup lang="ts">
import { ErrorMessage } from "@/api/client"
import { FlashMessageNotification } from "@/api/types"
import FlashMessage from "@/components/FlashMessage.vue"
import CenteredLayout from "@/layouts/CenteredLayout.vue"
import PrimaryButton from "@/components/PrimaryButton.vue"
import TextInput from "@/components/TextInput.vue"
import { useForm } from "@/composables/useForm"
import * as z from "zod"
import { ref } from "vue"
import { useAuth } from "@/composables/useAuth"
const auth = useAuth()
const formSchema = z
  .object({
    fullName: z.string(),
    email: z.string().min(1, "An email is required to continue").email("Please enter a valid email address."),
    password: z
      .string({
        required_error: "Password required to continue",
      })
      .min(6, "Password must be greater than 6 characters"),
    passwordConfirm: z.string({
      required_error: "Password is required to continue",
    }),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: "Passwords don't match",
    path: ["passwordConfirm"], // path of error
  })
const form = useForm(formSchema)
let flashMessage = ref<FlashMessageNotification>()

const { handleSubmit, isSubmitting } = form
const onSubmit = handleSubmit(async (values) => {
  const result = await auth.registerUser({ userCreate: values })
  if ((result as ErrorMessage).error) {
    form.setError(result as ErrorMessage)
  } else {
    console.log(auth.currentUser)
  }
})
</script>
