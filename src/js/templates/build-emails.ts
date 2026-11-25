/**
 * Build script for email templates.
 *
 * Uses Bun to compile TSX components and render to static HTML with all
 * styles inlined for email client compatibility.
 *
 * Output goes to src/py/app/server/static/email/ for wheel bundling.
 *
 * Usage: bun run build-emails.ts
 */

import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs"
import { basename, resolve } from "node:path"
import { render } from "@react-email/render"

const TEMPLATES_DIR = resolve(import.meta.dir, "src/emails")
const OUTPUT_DIR = resolve(import.meta.dir, "../../py/app/server/static/email")
const GLOBAL_CSS_PATH = resolve(import.meta.dir, "src/styles/global.css")

/**
 * Adds the optional global stylesheet to the document head.
 *
 * React Email already inlines component styles; this covers rules that
 * cannot be expressed inline.
 */
function inlineGlobalCss(html: string): string {
  if (!existsSync(GLOBAL_CSS_PATH)) {
    return html
  }

  const css = readFileSync(GLOBAL_CSS_PATH, "utf-8")
  if (!css.trim()) {
    return html
  }

  const styleTag = `<style type="text/css">\n${css}\n</style>`
  return html.replace("</head>", `${styleTag}\n</head>`)
}

async function buildTemplates() {
  console.log("📧 Building email templates...\n")

  mkdirSync(OUTPUT_DIR, { recursive: true })

  // A leading underscore marks a file that is not a standalone template.
  const templateFiles = readdirSync(TEMPLATES_DIR).filter((fileName) => fileName.endsWith(".tsx") && !fileName.startsWith("_"))

  let builtCount = 0
  let failedCount = 0

  for (const templateFile of templateFiles) {
    const templateName = basename(templateFile, ".tsx")

    try {
      const { default: Template } = await import(resolve(TEMPLATES_DIR, templateFile))

      if (!Template) {
        console.warn(`   ⚠ Warning: No default export in ${templateFile}, skipping`)
        continue
      }

      const html = inlineGlobalCss(await render(Template(), { pretty: true }))
      writeFileSync(resolve(OUTPUT_DIR, `${templateName}.html`), html, "utf-8")
      console.log(`   ✓ ${templateName}.html`)
      builtCount++
    } catch (error) {
      console.error(`   ✗ ${templateFile}:`, error instanceof Error ? error.message : error)
      failedCount++
    }
  }

  console.log(`\n✅ ${builtCount} templates built to: ${OUTPUT_DIR}`)

  if (failedCount > 0) {
    console.error(`❌ ${failedCount} template(s) failed to build`)
    process.exit(1)
  }
}

await buildTemplates()
