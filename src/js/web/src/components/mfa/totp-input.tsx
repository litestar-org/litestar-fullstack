import { Input } from "@/components/ui/input"

export const TOTP_CODE_LENGTH = 6

interface TotpInputProps {
  value: string
  onChange: (code: string) => void
  disabled?: boolean
  autoFocus?: boolean
}

export function TotpInput({ value, onChange, disabled, autoFocus }: Readonly<TotpInputProps>) {
  return (
    <Input
      autoFocus={autoFocus}
      autoComplete="one-time-code"
      inputMode="numeric"
      pattern="[0-9]*"
      placeholder="123456"
      value={value}
      onChange={(event) => onChange(event.target.value.replace(/\D/g, "").slice(0, TOTP_CODE_LENGTH))}
      disabled={disabled}
    />
  )
}
