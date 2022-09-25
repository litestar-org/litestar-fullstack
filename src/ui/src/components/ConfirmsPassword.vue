<script setup>
import { ref, reactive, nextTick } from "vue"
import DialogModal from "@/components/DialogModal.vue"
import TextInput from "@/components/TextInput.vue"
import SecondaryButton from "@/components/SecondaryButton.vue"

const emit = defineEmits(["confirmed"])

defineProps({
  title: {
    type: String,
    default: "Confirm Password",
  },
  content: {
    type: String,
    default: "For your security, please confirm your password to continue.",
  },
  button: {
    type: String,
    default: "Confirm",
  },
})

const confirmingPassword = ref(false)

const form = reactive({
  password: "",
  error: "",
  processing: false,
})

const passwordInput = ref(null)

const startConfirmingPassword = () => {
  axios.get(route("password.confirmation")).then((response) => {
    if (response.data.confirmed) {
      emit("confirmed")
    } else {
      confirmingPassword.value = true

      setTimeout(() => passwordInput.value.focus(), 250)
    }
  })
}

const confirmPassword = () => {
  form.processing = true

  axios
    .post(route("password.confirm"), {
      password: form.password,
    })
    .then(() => {
      form.processing = false

      closeModal()
      nextTick().then(() => emit("confirmed"))
    })
    .catch((error) => {
      form.processing = false
      form.error = error.response.data.errors.password[0]
      passwordInput.value.focus()
    })
}

const closeModal = () => {
  confirmingPassword.value = false
  form.password = ""
  form.error = ""
}
</script>

<template>
  <span>
    <span @click="startConfirmingPassword">
      <slot />
    </span>

    <dialog-modal :show="confirmingPassword" @close="closeModal">
      <template #title>
        {{ title }}
      </template>

      <template #content>
        {{ content }}

        <div class="mt-4">
          <text-input
            ref="passwordInput"
            name="password"
            type="password"
            placeholder="Current password"
            autocomplete="off"
            :error-message="getFieldError('password')"
            @keyup.enter="confirmPassword"
          />
          <JetInput
            ref="passwordInput"
            v-model="form.password"
            type="password"
            class="mt-1 block w-3/4"
            placeholder="Password"
            @keyup.enter="confirmPassword"
          />

          <JetInputError :message="form.error" class="mt-2" />
        </div>
      </template>

      <template #footer>
        <secondary-button @click="closeModal">Cancel</secondary-button>

        <primary-button
          class="ml-3"
          :class="{ 'opacity-25': form.processing }"
          :disabled="form.processing"
          @click="confirmPassword"
        >
          {{ button }}
        </primary-button>
      </template>
    </dialog-modal>
  </span>
</template>
