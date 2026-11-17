import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const SERVER = 'http://localhost:8000';

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			// One page that finds its own screens; the server answers every path with it (011).
			adapter: adapter({ fallback: 'index.html' })
		})
	],
	server: { proxy: { '/api': SERVER } }
});
