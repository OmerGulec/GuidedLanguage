<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
		/** The screen's keys: after the content, and on a phone held at the bottom. */
		actions?: Snippet;
	}

	let { children, actions }: Props = $props();
</script>

<div class="content">{@render children()}</div>
{#if actions !== undefined}
	<div class="actions">{@render actions()}</div>
{/if}

<style>
	.content {
		margin-top: var(--space-5);
	}

	.actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: var(--space-3) var(--space-5);
		margin-top: var(--space-5);
	}

	@media (max-width: 640px) {
		.content {
			flex: 1;
			margin-top: var(--space-4);
		}

		.actions {
			position: sticky;
			bottom: 0;
			gap: var(--space-2) var(--space-3);
			margin: var(--space-4) calc(-1 * var(--gutter)) 0;
			padding: var(--space-3) var(--gutter);
			background: var(--paper);
		}
	}
</style>
