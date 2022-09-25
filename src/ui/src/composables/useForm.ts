/* eslint-disable @typescript-eslint/ban-ts-comment */
import { ErrorMessage, FieldError } from "@/api/client"
import { reactive, readonly, ref } from "vue"
import * as zod from "zod"

export type Field<Value> = {
  /**
   * Gets the name of the field
   */
  name: string
  /**
   * Gets the error for the field
   */
  error?: string
  /**
   * Gets the value for the field
   */
  value?: Value
  /**
   * Event handler for value change event
   */
  onChange(value?: Value): void
  /**
   * Event handler for blur event
   */
  onBlur(): void
  /**
   * Sets the field as being touched
   */
  touch(): void
}

export const useForm = <
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Schema extends zod.ZodObject<any> | zod.ZodEffects<zod.ZodObject<any>>,
  Values extends zod.infer<Schema>,
  FieldNames extends keyof Values
>(
  schema: Schema,
  options?: {
    initialValues?: Partial<Values>
  }
) => {
  const values = reactive<Partial<Values>>(options?.initialValues ?? {})
  const readonlyValues = readonly(values)

  type Touched = { [x in FieldNames]?: boolean }
  const touched = reactive<Touched>({})

  type Errors = { [x in FieldNames]?: string }
  const errors = ref<Errors>({})

  const submitted = ref(false)

  const isSubmitting = ref(false)

  const validate = (): boolean => {
    const result = schema.safeParse(values)
    if (result.success === false) {
      const fieldErrors = result.error.flatten().fieldErrors
      errors.value = Object.keys(fieldErrors).reduce<Errors>((acc, cur) => {
        const key = cur as FieldNames
        // @ts-ignore - The TS engine finds this expression too complex to resolve
        if (submitted.value || touched[key]) {
          const val = fieldErrors[cur]
          if (val !== undefined) {
            acc[key] = val[0]
          }
        }
        return acc
      }, {})
    } else {
      errors.value = {}
    }
    return result.success
  }

  const setError = (res: ErrorMessage) => {
    const fieldErrors = res.error.form?.fieldErrors
    if (fieldErrors) {
      errors.value = fieldErrors.reduce<Errors>((acc: Errors, cur: FieldError) => {
        const key = cur.fieldName as FieldNames
        acc[key] = cur.message
        return acc
      }, {})
    }
  }
  const field = <FieldId extends FieldNames, Value extends Values[FieldId]>(field: FieldId) => {
    return {
      get name() {
        return field
      },
      get error(): string | undefined {
        return errors.value[field]
      },

      get value(): Value | undefined {
        // @ts-ignore - The TS engine finds this expression too complex to resolve
        return readonlyValues[field]
      },

      onChange: (value?: Value) => {
        // @ts-ignore - The TS engine finds this expression too complex to resolve
        values[field] = value
        // @ts-ignore - The TS engine finds this expression too complex to resolve
        if (submitted.value || touched[field]) {
          validate()
        }
      },

      onBlur: () => {
        // @ts-ignore - The TS engine finds this expression too complex to resolve
        touched[field] = true
        validate()
      },

      touch() {
        // @ts-ignore - The TS engine finds this expression too complex to resolve
        touched[field] = true
      },
    } as Field<Value>
  }

  return {
    errors,
    isSubmitting,
    values: readonlyValues,
    field,
    handleSubmit: (onSubmit: (values: Values) => void) => {
      return async (event: Event) => {
        event.preventDefault()
        submitted.value = true
        const isValid = validate()
        if (isValid) {
          isSubmitting.value = true
          try {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            await Promise.resolve(onSubmit(readonlyValues as any as Values))
          } finally {
            isSubmitting.value = false
          }
        }
      }
    },
    setError,
  }
}
