import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/kit/vite';

/**
 * @param {string} path
 */
function getBackendUrl(path) {
	return `${process.env.FRONTEND_URL || 'http://localhost:8000'}${path}`;
}
const STATIC_URL = process.env.STATIC_URL || '/static/';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// adapter-auto only supports some environments, see https://kit.svelte.dev/docs/adapter-auto for a list.
		// If your environment is not supported or you settled on a specific environment, switch out the adapter.
		// See https://kit.svelte.dev/docs/adapters for more information about adapters.
		adapter: adapter(),
		files: {
			assets: 'src/app/domain/web/resources/assets',
			lib: 'src/app/domain/web/resources/lib',
			hooks: {
				client: 'src/app/domain/web/resources/hooks/client',
				server: 'src/app/domain/web/resources/hooks/server'
			},
			serviceWorker: 'src/app/domain/web/resources/service-worker',
			appTemplate: 'src/app/domain/web/resources/app.html',
			errorTemplate: 'src/app/domain/web/resources/error.html',
			params: 'src/app/domain/web/resources/params',
			routes: 'src/app/domain/web/resources/routes'
		},
		outDir: 'src/app/domain/web/public/'
	}
};

export default config;
