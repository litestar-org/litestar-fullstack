import { createClient } from "@hey-api/openapi-ts"
import type { UserConfig } from "@hey-api/openapi-ts"
import config from "../openapi.config"

async function main() {
  await createClient(config as UserConfig)
}

main().catch(console.error)
