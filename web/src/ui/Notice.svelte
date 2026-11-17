<script lang="ts">
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<div role="alert">{@render children()}</div>

<style>
	div {
		padding: var(--space-2) var(--space-3);
		border: var(--rule-light) solid var(--ink);
	}
</style>
