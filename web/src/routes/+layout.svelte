<script lang="ts">
	import '../ui/tokens.css';

	import { page } from '$app/state';
	import type { Snippet } from 'svelte';

	import Frame from '../ui/Frame.svelte';
	import Notice from '../ui/Notice.svelte';

	let { children }: { children: Snippet } = $props();

	const PLACES = [
		{ name: 'Today', href: '/' },
		{ name: 'Library', href: '/library' },
		{ name: 'Dictionary', href: '/dictionary' },
		{ name: 'You', href: '/you' }
	];

	// Review is part of the day's work, so it stays under Today.
	const current = $derived(page.url.pathname === '/review' ? '/' : page.url.pathname);

	// Every failed request ends here, the one place network failures are handled.
	let failed = $state(false);
</script>

<svelte:window onunhandledrejection={() => (failed = true)} />

<Frame places={page.url.pathname === '/sign-in' ? [] : PLACES} {current}>
	{#if failed}
		<Notice>The server did not answer as expected. Check that it is running, then reload.</Notice>
	{/if}
	{@render children()}
</Frame>
