<template>
  <centered-layout>
    <div class="flex min-h-screen items-center justify-center bg-base-200 px-4 dark:bg-base-200-dark">
      <div class="w-full max-w-md">
        <application-logo class="h-32 w-full flex-row pb-4"></application-logo>

        <h2 class="text-content-base mb-8 text-center text-3xl font-extrabold">Starlite Application</h2>

        <form class="space-y-4" @submit="onSubmit">
          <text-input name="password" type="password" label="Password" autocomplete="off"></text-input>
          <text-input name="passwordConfirm" type="password" label="Confirm Password" autocomplete="off"></text-input>

          <div class="flex items-center justify-between text-sm">
            <router-link to="/register" class="link link-hover">Need an account?</router-link>
            <router-link to="/login" class="link link-hover">Already have an account?</router-link>
          </div>

          <div>
            <PrimaryButton type="submit" :disabled="isSubmitting" class="w-full" size="lg">
              Update Password
            </PrimaryButton>
          </div>
        </form>
      </div>
    </div>
  </centered-layout>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router"
import { AccountApiResetPasswordRequest, ErrorMessage } from "@/api/client"
import CenteredLayout from "@/layouts/CenteredLayout.vue"
import * as z from "zod"
import PrimaryButton from "@/components/PrimaryButton.vue"
import { useAuth } from "@/composables/useAuth"
import { useForm } from "@/composables/useForm"

const formSchema = z
  .object({
    token: z.string({ required_error: "Missing reset token." }),
    newPassword: z.string().min(1, "Password is required").min(6, "Password must be greater than 6 characters"),
    newPasswordConfirm: z.string().min(1, "Password is required to continue"),
  })
  .refine((data) => data.newPassword === data.newPasswordConfirm, {
    message: "Passwords don't match",
    path: ["newPasswordConfirm"],
  })

const route = useRoute()
const auth = useAuth()
const form = useForm(formSchema)

const { handleSubmit, isSubmitting } = form
const onSubmit = handleSubmit(async (values) => {
  const result = await auth.resetPassword({
    userPasswordReset: { token: route.params.token, newPassword: values.newPassword },
  } as AccountApiResetPasswordRequest)
  if ((result as ErrorMessage).error) {
    form.setError(result as ErrorMessage)
  } else {
    console.log(auth.currentUser)
  }
})
</script>
