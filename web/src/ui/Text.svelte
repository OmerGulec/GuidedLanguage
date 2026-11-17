<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		size?: 'small' | 'body' | 'lead' | 'title';
		italic?: boolean;
		bold?: boolean;
		/** Line breaks as written, for text that arrives laid out. */
		verbatim?: boolean;
		children: Snippet;
	}

	let {
		size = 'body',
		italic = false,
		bold = false,
		verbatim = false,
		children
	}: Props = $props();
</script>

<p class={size} class:italic class:bold class:verbatim>{@render children()}</p>

<style>
	p {
		margin: 0;
		max-width: 38em;
	}

	.small {
		font-size: var(--type-small);
	}

	.lead {
		font-size: var(--type-lead);
	}

	.title {
		font-size: var(--type-title);
		line-height: 1.2;
	}

	.italic {
		font-style: italic;
	}

	.bold {
		font-weight: 700;
	}

	.verbatim {
		white-space: pre-wrap;
	}
</style>
