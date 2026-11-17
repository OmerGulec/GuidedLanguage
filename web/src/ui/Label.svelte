<script lang="ts">
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<span>{@render children()}</span>

<style>
	span {
		font-size: var(--type-label);
		font-variant-caps: all-small-caps;
		letter-spacing: var(--tracking-label);
	}
</style>
