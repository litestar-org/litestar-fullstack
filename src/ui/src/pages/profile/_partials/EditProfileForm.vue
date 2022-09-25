<template>
  <form-panel id="profileUpdateForm" class="mb-6 px-4 pb-4 sm:px-6 lg:px-8" @valid-submit="onSubmit">
    <template #title>User Details</template>
    <template #description>Update the information associated with your account.</template>
    <template #form>
      <!--FormKit-->
      <div class="col-span-6 xl:col-span-3">
        <text-input
          name="fullName"
          type="text"
          label="Name"
          placeholder="Full Name"
          :value="auth.currentUser.fullName"
        />
      </div>
      <div class="col-span-6 xl:col-span-3">
        <text-input
          name="email"
          type="email"
          label="Email"
          placeholder="Email Address"
          :value="auth.currentUser.email"
        />
      </div>
    </template>

    <template #actions>
      <primary-button size="md" type="submit" :disabled="isSubmitting">Save Profile Changes</primary-button>
    </template>
  </form-panel>
</template>
<script setup lang="ts">
import { ErrorMessage } from "@/api/client"
import FormPanel from "@/components/FormPanel.vue"
import TextInput from "@/components/TextInput.vue"
import PrimaryButton from "@/components/PrimaryButton.vue"
import * as z from "zod"
import { useForm } from "@/composables/useForm"
import { useAuth } from "@/composables/useAuth"
const auth = useAuth()
const formSchema = z.object({
  fullName: z.string().optional(),
  email: z.string({ required_error: "Email is required." }).email("A valid email address is required."),
})
const form = useForm(formSchema)
const { handleSubmit, isSubmitting } = form
const onSubmit = handleSubmit(async (values) => {
  const result = await auth.updateProfile({ userUpdate: values })
  if ((result as ErrorMessage).error) {
    form.setError(result as ErrorMessage)
  } else {
    console.log("updated profile")
  }
})
</script>
