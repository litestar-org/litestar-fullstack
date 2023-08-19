import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'path';
function getBackendUrl(path: string) {
	return `${process.env.FRONTEND_URL || 'http://localhost:8000'}${path}`;
}
export default defineConfig({
	plugins: [sveltekit()],
	server: {
		fs: {
			allow: ['.', path.join(__dirname, 'node_modules')]
		},
		host: '0.0.0.0',
		port: 3005,
		cors: true,
		strictPort: true,
		watch: {
			ignored: ['node_modules', '.venv', '**/__pycache__/**']
		},
		proxy: {
			'/api': {
				target: getBackendUrl('/api'),
				changeOrigin: true,
				ws: true,
				rewrite: (path) => path.replace(/^\/api/, '')
			}
		}
	},
	resolve: {
		alias: {
			'@': path.resolve(__dirname, 'src/app/domain/web/resources')
		}
	}
});
