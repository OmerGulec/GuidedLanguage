<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		size?: 'body' | 'lead' | 'title' | 'word';
		children: Snippet;
	}

	let { size = 'body', children }: Props = $props();
</script>

<span lang="ja" class={size}>{@render children()}</span>

<style>
	span {
		font-family: var(--mincho);
	}

	.lead {
		font-size: var(--type-lead);
	}

	.title {
		font-size: var(--type-title);
	}

	.word {
		display: block;
		font-size: var(--type-word);
		line-height: 1.1;
	}
</style>
