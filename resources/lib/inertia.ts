import { Head, Link, useForm } from "@inertiajs/react"
import { ZodIssue, ZodObject, ZodRawShape } from "zod"
import { watch, computed } from "vue"

const parseErrors = <T>(issues: ZodIssue[]) => {
  return issues.reduce(
    (pre, curr) => ({
      ...pre,
      [curr.path.join(".")]: curr.message,
    }),
    {} as Record<keyof T, string>
  )
}

export const useZodForm: <
  T extends Record<string, unknown>,
  U extends ZodRawShape,
>(
  formData: T,
  zodSchema: ZodObject<U>,
  rememberKey?: string
) => InertiaForm<T> & { errors: Record<string, string | undefined> } = <
  T extends Record<string, unknown>,
  U extends ZodRawShape,
>(
  formData: T,
  zodSchema: ZodObject<U>,
  rememberKey?: string
) => {
  const inertiaForm = rememberKey
    ? useForm<T>(rememberKey, formData)
    : useForm<T>(formData)
  type FormType = typeof inertiaForm
  const data = computed(() => inertiaForm.data())
  watch(data, (val, oldVal) => {
    const diffs = Object.entries(val).filter(([k, v]) => oldVal[k] !== v)
    diffs.forEach(([k, v]) => {
      const pickedField = zodSchema.pick({ [k as any]: true })
      const result = pickedField.safeParse({ [k]: v })
      if (!result.success) {
        const errors = parseErrors<T>(result.error.issues)
        inertiaForm.setError({ ...inertiaForm.errors, ...errors })
      } else {
        delete inertiaForm.errors[k]
      }
    })
  })
  return new Proxy<FormType & { errors: Record<string, string | undefined> }>(
    inertiaForm,
    {
      get(target, prop) {
        if (prop === "submit") {
          inertiaForm.clearErrors()
          const result = zodSchema.safeParse(inertiaForm.data())

          if (!result.success) {
            const errors = parseErrors<T>(result.error.issues)
            inertiaForm.setError(errors)
            return () => {}
          }
        }
        return target[prop.toString()]
      },
    }
  )
}
