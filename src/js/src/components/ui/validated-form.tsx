/**
 * Validated form component with real-time validation
 */

import { Button } from "@/components/ui/button"
import ValidatedInput from "@/components/ui/validated-input"
import useValidation, { type ValidationRule, type ValidationRules, validateEmail, validatePassword, validateUsername, validatePhone, validateName } from "@/hooks/use-validation"
import { cn } from "@/lib/utils"
import React, { useCallback, useEffect } from "react"

export interface FormField {
  name: string
  label: string
  type?: "text" | "email" | "password" | "tel" | "url"
  placeholder?: string
  validationRule?: ValidationRule
  showPasswordStrength?: boolean
  helperText?: string
  autoComplete?: string
}

export interface ValidatedFormProps {
  fields: FormField[]
  initialValues?: Record<string, any>
  onSubmit: (values: Record<string, any>, isValid: boolean) => void
  submitLabel?: string
  submitDisabled?: boolean
  className?: string
  children?: React.ReactNode
  validateOnSubmit?: boolean
}

// Pre-defined validation rules for common field types
const getDefaultValidationRule = (field: FormField): ValidationRule => {
  const baseRule: ValidationRule = {
    required: true,
  }

  switch (field.type) {
    case "email":
      return {
        ...baseRule,
        custom: validateEmail,
      }

    case "password":
      return {
        ...baseRule,
        custom: validatePassword,
      }

    default:
      // Infer from field name
      if (field.name.toLowerCase().includes("email")) {
        return {
          ...baseRule,
          custom: validateEmail,
        }
      }
      if (field.name.toLowerCase().includes("password")) {
        return {
          ...baseRule,
          custom: validatePassword,
        }
      }
      if (field.name.toLowerCase().includes("username")) {
        return {
          ...baseRule,
          custom: validateUsername,
        }
      }
      if (field.name.toLowerCase().includes("phone")) {
        return {
          ...baseRule,
          custom: validatePhone,
        }
      }
      if (field.name.toLowerCase().includes("name")) {
        return {
          ...baseRule,
          custom: validateName,
        }
      }

      return baseRule
  }
}

export function ValidatedForm({
  fields,
  initialValues = {},
  onSubmit,
  submitLabel = "Submit",
  submitDisabled = false,
  className,
  children,
  validateOnSubmit = true,
}: ValidatedFormProps) {
  // Initialize form data
  const [formData, setFormData] = React.useState<Record<string, any>>(() => {
    const data: Record<string, any> = {}
    fields.forEach((field) => {
      data[field.name] = initialValues[field.name] || ""
    })
    return data
  })

  // Build validation rules
  const validationRules: ValidationRules = React.useMemo(() => {
    const rules: ValidationRules = {}
    fields.forEach((field) => {
      rules[field.name] = field.validationRule || getDefaultValidationRule(field)
    })
    return rules
  }, [fields])

  // Use validation hook
  const { errors, isValid, validate } = useValidation(formData, validationRules)

  // Update form data
  const updateField = useCallback((name: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }, [])

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (validateOnSubmit) {
      const formIsValid = validate()
      onSubmit(formData, formIsValid)
    } else {
      onSubmit(formData, isValid)
    }
  }

  // Sync external initial values
  useEffect(() => {
    if (Object.keys(initialValues).length > 0) {
      setFormData((prev) => ({
        ...prev,
        ...initialValues,
      }))
    }
  }, [initialValues])

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-6", className)} noValidate>
      {/* Form fields */}
      <div className="space-y-4">
        {fields.map((field) => (
          <ValidatedInput
            key={field.name}
            label={field.label}
            type={field.type}
            placeholder={field.placeholder}
            value={formData[field.name]}
            error={errors[field.name]}
            validationRule={field.validationRule || getDefaultValidationRule(field)}
            showPasswordStrength={field.showPasswordStrength}
            helperText={field.helperText}
            autoComplete={field.autoComplete}
            onChange={(value) => updateField(field.name, value)}
          />
        ))}
      </div>

      {/* Custom children (additional form elements) */}
      {children}

      {/* Submit button */}
      <Button type="submit" disabled={submitDisabled || (validateOnSubmit ? false : !isValid)} className="w-full">
        {submitLabel}
      </Button>
    </form>
  )
}

// Example usage component
export function ExampleRegistrationForm() {
  const handleSubmit = (values: Record<string, any>, isValid: boolean) => {
    if (isValid) {
      console.log("Form submitted:", values)
    } else {
      console.log("Form has errors")
    }
  }

  const fields: FormField[] = [
    {
      name: "name",
      label: "Full Name",
      type: "text",
      placeholder: "Enter your full name",
      helperText: "This will be displayed on your profile",
    },
    {
      name: "email",
      label: "Email Address",
      type: "email",
      placeholder: "Enter your email",
      autoComplete: "email",
    },
    {
      name: "username",
      label: "Username",
      type: "text",
      placeholder: "Choose a username",
      helperText: "3-30 characters, letters, numbers, hyphens, and underscores only",
    },
    {
      name: "password",
      label: "Password",
      type: "password",
      placeholder: "Create a strong password",
      showPasswordStrength: true,
      autoComplete: "new-password",
    },
    {
      name: "phone",
      label: "Phone Number",
      type: "tel",
      placeholder: "+1 (555) 123-4567",
      helperText: "Optional - for account recovery",
      validationRule: {
        required: false,
        custom: validatePhone,
      },
    },
  ]

  return (
    <div className="max-w-md mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Create Account</h2>
      <ValidatedForm fields={fields} onSubmit={handleSubmit} submitLabel="Create Account" />
    </div>
  )
}

export default ValidatedForm
