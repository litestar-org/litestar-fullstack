# Tailwind CSS v4 Skill

Quick reference for Tailwind CSS v4 patterns.

## Context7 Lookup

```python
mcp__context7__resolve-library-id(libraryName="tailwind css", query="...")
mcp__context7__query-docs(libraryId="/tailwindlabs/tailwindcss", query="...")
```

## Project Files

- Styles: `src/js/src/styles.css`
- Config: Using Tailwind v4 CSS-based config
- Components: `src/js/src/components/ui/`

## Tailwind v4 Changes

Tailwind v4 uses CSS-based configuration:

```css
/* styles.css */
@import "tailwindcss";

@theme {
  --color-primary: oklch(0.5 0.2 240);
  --radius-lg: 0.5rem;
}
```

## Common Utility Classes

### Layout

```tsx
// Flexbox
<div className="flex items-center justify-between gap-4">

// Grid
<div className="grid grid-cols-3 gap-4">

// Container
<div className="container mx-auto px-4">
```

### Spacing

```tsx
// Padding
<div className="p-4 px-6 py-2">

// Margin
<div className="m-4 mx-auto my-2">

// Gap
<div className="gap-4 gap-x-2 gap-y-4">
```

### Typography

```tsx
<h1 className="text-4xl font-bold tracking-tight">
<p className="text-muted-foreground text-sm">
<span className="font-medium">
```

### Colors

```tsx
// Background
<div className="bg-background bg-primary bg-muted">

// Text
<span className="text-foreground text-primary text-muted-foreground">

// Border
<div className="border border-border border-primary">
```

### Sizing

```tsx
// Width/Height
<div className="w-full h-screen w-64 h-12">

// Max/Min
<div className="max-w-md min-h-screen">
```

### Borders

```tsx
<div className="rounded-lg border border-border shadow-sm">
<div className="rounded-full">
```

### Interactive States

```tsx
<button className="hover:bg-primary/90 focus:ring-2 focus:ring-primary disabled:opacity-50">
<a className="hover:underline">
```

## Shadcn/ui Component Patterns

```tsx
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

// Button variants
<Button variant="default">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Destructive</Button>

// Button sizes
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>

// Card
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
</Card>
```

## Dark Mode

```tsx
// Automatic with system preference
<div className="bg-background text-foreground">

// Force dark
<div className="dark">
  <div className="bg-background"> {/* Uses dark theme colors */}
```

## Responsive Design

```tsx
// Mobile-first breakpoints
<div className="w-full md:w-1/2 lg:w-1/3">

// Hide/show
<div className="hidden md:block">
<div className="block md:hidden">
```

## Animation

```tsx
// Built-in
<div className="animate-spin animate-pulse animate-bounce">

// Transitions
<div className="transition-colors duration-200 ease-in-out">
```

## Custom Classes with cn()

```tsx
import { cn } from "@/lib/utils"

interface Props {
  className?: string
}

function Component({ className }: Props) {
  return (
    <div className={cn(
      "flex items-center p-4 rounded-lg",
      "bg-background border border-border",
      className
    )}>
      Content
    </div>
  )
}
```

## Form Styling

```tsx
<form className="space-y-4">
  <div className="space-y-2">
    <label className="text-sm font-medium">Email</label>
    <Input type="email" placeholder="email@example.com" />
  </div>
  <Button type="submit" className="w-full">
    Submit
  </Button>
</form>
```
