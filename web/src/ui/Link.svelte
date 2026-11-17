<script lang="ts">
	import type { Snippet } from 'svelte';

	import { keyName, shortcut as onKey } from './shortcut';

	interface Props {
		href?: string;
		onpress?: () => void;
		shortcut?: string;
		children: Snippet;
	}

	let { href, onpress, shortcut, children }: Props = $props();
</script>

<svelte:window
	onkeydown={shortcut === undefined || onpress === undefined ? undefined : onKey(shortcut, onpress)}
/>

{#if href !== undefined}
	<a {href}>{@render children()}</a>
{:else}
	<button type="button" onclick={onpress}>
		{@render children()}
		{#if shortcut !== undefined}<kbd>{keyName(shortcut)}</kbd>{/if}
	</button>
{/if}

<style>
	a,
	button {
		display: inline-flex;
		align-items: center;
		gap: var(--space-2);
		min-height: var(--tap-height);
		padding: 0;
		border: 0;
		background: none;
		color: var(--ink);
		font-family: var(--serif);
		font-size: var(--type-label);
		font-variant-caps: all-small-caps;
		letter-spacing: var(--tracking-label);
		text-decoration: underline;
		text-underline-offset: 4px;
		cursor: pointer;
	}

	a:hover,
	button:hover {
		color: var(--ink-hover);
	}

	kbd {
		padding: 0 0.4em 0.1em;
		border: 1px solid currentColor;
		font-family: var(--serif);
		font-size: var(--type-small);
	}

	@media (hover: none) {
		kbd {
			display: none;
		}
	}
</style>
