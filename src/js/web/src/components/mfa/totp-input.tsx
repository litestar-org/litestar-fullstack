import { Input } from "@/components/ui/input"

interface TotpInputProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  autoFocus?: boolean
}

export function TotpInput({ value, onChange, disabled, autoFocus }: TotpInputProps) {
  return (
    <Input
      autoFocus={autoFocus}
      autoComplete="one-time-code"
      inputMode="numeric"
      pattern="[0-9]*"
      placeholder="123456"
      value={value}
      onChange={(event) => {
        const next = event.target.value.replace(/\D/g, "").slice(0, 6)
        onChange(next)
      }}
      disabled={disabled}
    />
  )
}
