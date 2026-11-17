<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		gap?: 'tight' | 'normal' | 'loose';
		/** No wider than a form reads well. */
		narrow?: boolean;
		children: Snippet;
	}

	let { gap = 'normal', narrow = false, children }: Props = $props();
</script>

<div class={gap} class:narrow>{@render children()}</div>

<style>
	div {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		min-width: 0;
	}

	.tight {
		gap: var(--space-2);
	}

	.normal {
		gap: var(--space-4);
	}

	.loose {
		gap: var(--space-5);
	}

	.narrow {
		max-width: 24rem;
		align-items: stretch;
	}
</style>
