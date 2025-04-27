import { createClient } from '@hey-api/openapi-ts';
import config from '../hey-api.config';

async function main() {
  await createClient(config);
}

main().catch(console.error);
