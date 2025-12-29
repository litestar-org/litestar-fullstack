/**
 * Build script for email templates.
 *
 * Uses Bun to compile TSX components and render to static HTML with all
 * styles inlined for email client compatibility.
 *
 * Output goes to src/py/app/templates/email/ for wheel bundling.
 *
 * Usage: bun run build-emails.ts
 */

import { render } from "@react-email/render"
import { writeFileSync, mkdirSync, readdirSync, readFileSync, existsSync } from "node:fs"
import { resolve, basename } from "node:path"

// Output directory (inside Python package for wheel bundling)
const OUTPUT_DIR = resolve(import.meta.dir, "../../py/app/templates/email")

// Optional global CSS file for additional styles
const GLOBAL_CSS_PATH = resolve(import.meta.dir, "src/styles/global.css")

// Ensure output directory exists
mkdirSync(OUTPUT_DIR, { recursive: true })

// Discover email templates
const emailsDir = resolve(import.meta.dir, "src/emails")

/**
 * Inline CSS into HTML head if a global CSS file exists.
 * React Email already inlines component styles, but this allows
 * for additional global styles if needed.
 */
function inlineGlobalCSS(html: string): string {
  if (!existsSync(GLOBAL_CSS_PATH)) {
    return html
  }

  const css = readFileSync(GLOBAL_CSS_PATH, "utf-8")
  if (!css.trim()) {
    return html
  }

  // Insert CSS into head
  const styleTag = `<style type="text/css">\n${css}\n</style>`
  return html.replace("</head>", `${styleTag}\n</head>`)
}

async function buildTemplates() {
  console.log("📧 Building email templates...\n")

  const templateFiles = readdirSync(emailsDir).filter(
    (f) => f.endsWith(".tsx") && !f.startsWith("_")
  )

  let successCount = 0
  let failCount = 0

  for (const file of templateFiles) {
    const name = basename(file, ".tsx")
    const modulePath = resolve(emailsDir, file)

    try {
      // Dynamic import the TSX file (Bun handles this natively)
      const module = await import(modulePath)
      const Component = module.default

      if (!Component) {
        console.warn(`   ⚠ Warning: No default export in ${file}, skipping`)
        continue
      }

      // Render to static HTML with react-email (all styles inlined)
      let html = await render(Component(), {
        pretty: true,
      })

      // Optionally inline global CSS
      html = inlineGlobalCSS(html)

      const outputPath = resolve(OUTPUT_DIR, `${name}.html`)
      writeFileSync(outputPath, html, "utf-8")
      console.log(`   ✓ ${name}.html`)
      successCount++
    } catch (error) {
      console.error(`   ✗ ${file}:`, error instanceof Error ? error.message : error)
      failCount++
    }
  }

  console.log(`\n✅ ${successCount} templates built to: ${OUTPUT_DIR}`)

  if (failCount > 0) {
    console.error(`❌ ${failCount} template(s) failed to build`)
    process.exit(1)
  }
}

buildTemplates()
