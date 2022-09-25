<template>
  <form-panel id="passwordUpdateForm" class="px-4 pb-4 sm:px-6 lg:px-8" @valid-submit="onSubmit">
    <template #title>Credentials</template>
    <template #description>Update your password associated with your account.</template>
    <template #form>
      <!--FormKit-->
      <div class="col-span-6 xl:col-span-3">
        <text-input
          name="currentPassword"
          type="password"
          label="Password"
          placeholder="Current password"
          autocomplete="off"
        />
      </div>
      <div class="col-span-6 xl:col-span-3">
        <text-input
          name="newPassword"
          type="password"
          label="New Password"
          placeholder="New Password"
          autocomplete="off"
        />
        <text-input name="newPasswordConfirm" type="password" placeholder="Confirm New Password" autocomplete="off" />
      </div>
    </template>

    <template #actions>
      <primary-button size="md" type="submit" :disabled="isSubmitting">Update Password</primary-button>
    </template>
  </form-panel>
</template>
<script setup lang="ts">
import { useForm } from "@/composables/useForm"
import { useAuth } from "@/composables/useAuth"
import { ErrorMessage } from "@/api/client"
import FormPanel from "@/components/FormPanel.vue"
import PrimaryButton from "@/components/PrimaryButton.vue"
import TextInput from "@/components/TextInput.vue"
import * as z from "zod"
const auth = useAuth()
const formSchema = z
  .object({
    currentPassword: z.string({ required_error: "Password is required to continue." }),
    newPassword: z
      .string({ required_error: "Password is required to continue." })
      .min(6, "Password must be greater than 6 characters"),
    newPasswordConfirm: z.string({ required_error: "Password is required to continue." }),
  })
  .refine((data) => data.newPassword === data.newPasswordConfirm, {
    message: "Passwords don't match",
    path: ["newPasswordConfirm"], // path of error
  })
const form = useForm(formSchema)
const { handleSubmit, isSubmitting } = form
const onSubmit = handleSubmit(async (values) => {
  const result = await auth.updatePassword({ userPasswordUpdate: values })
  if ((result as ErrorMessage).error) {
    form.setError(result as ErrorMessage)
  } else {
    console.log("updated password")
  }
})
</script>
