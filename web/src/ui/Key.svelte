<script lang="ts">
	import type { Snippet } from 'svelte';

	import { keyName, shortcut as onKey } from './shortcut';

	interface Props {
		onpress?: () => void;
		/** A key of the keyboard that presses this one, shown beside the label. */
		shortcut?: string;
		/** The second of two answers: an outline, so the eye lands on the first. */
		quiet?: boolean;
		submit?: boolean;
		disabled?: boolean;
		children: Snippet;
	}

	let {
		onpress,
		shortcut,
		quiet = false,
		submit = false,
		disabled = false,
		children
	}: Props = $props();

	const press = (): void => {
		if (!disabled) onpress?.();
	};
</script>

<svelte:window onkeydown={shortcut === undefined ? undefined : onKey(shortcut, press)} />

<button type={submit ? 'submit' : 'button'} class:quiet {disabled} onclick={onpress}>
	{@render children()}
	{#if shortcut !== undefined}<kbd>{keyName(shortcut)}</kbd>{/if}
</button>

<style>
	button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-3);
		min-height: var(--key-height);
		padding: 0 var(--space-5);
		border: 0;
		border-radius: 0;
		background: var(--ink);
		color: var(--paper);
		box-shadow:
			inset 0 0 0 4px var(--ink),
			inset 0 0 0 5px var(--paper);
		font-family: var(--serif);
		font-size: var(--type-lead);
		font-weight: 700;
		white-space: nowrap;
		cursor: pointer;
	}

	button:active,
	.quiet {
		background: var(--paper);
		color: var(--ink);
		box-shadow: inset 0 0 0 2px var(--ink);
	}

	.quiet:active {
		background: var(--ink);
		color: var(--paper);
	}

	button:focus-visible {
		outline: 2px solid var(--ink);
		outline-offset: 3px;
	}

	button:disabled {
		opacity: 0.5;
		cursor: default;
	}

	kbd {
		padding: 0 0.4em 0.1em;
		border: 1px solid currentColor;
		font-family: var(--serif);
		font-size: var(--type-small);
		font-weight: 400;
		font-variant-caps: all-small-caps;
		letter-spacing: var(--tracking-label);
	}

	/* A hint only where a keyboard is in use. */
	@media (hover: none) {
		kbd {
			display: none;
		}
	}

	@media (max-width: 640px) {
		button {
			flex: 1;
		}
	}
</style>
