<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Place {
		name: string;
		href: string;
	}

	interface Props {
		places: Place[];
		current: string;
		children: Snippet;
	}

	let { places, current, children }: Props = $props();
</script>

<div class="frame">
	<nav aria-label="Main">
		{#each places as place (place.href)}
			<a href={place.href} aria-current={place.href === current ? 'page' : undefined}>
				{place.name}
			</a>
		{/each}
	</nav>
	<main>
		<div class="page">{@render children()}</div>
	</main>
</div>

<style>
	.frame {
		display: flex;
		flex-direction: column;
		min-height: 100dvh;
	}

	nav,
	.page {
		box-sizing: border-box;
		width: 100%;
		max-width: calc(var(--page-width) + 2 * var(--gutter));
		margin: 0 auto;
		padding: 0 var(--gutter);
	}

	nav {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-1) var(--space-4);
		padding-top: var(--space-3);
		font-size: var(--type-label);
		font-variant-caps: all-small-caps;
		letter-spacing: var(--tracking-label);
	}

	a {
		padding: 0.1em 0.6em 0.2em;
		color: var(--ink);
		text-decoration: none;
	}

	a:hover {
		color: var(--ink-hover);
	}

	a[aria-current='page'] {
		background: var(--ink);
		color: var(--paper);
	}

	main {
		flex: 1;
		padding-bottom: var(--space-6);
	}

	@media (max-width: 640px) {
		.frame {
			height: 100dvh;
		}

		nav {
			order: 2;
			flex: none;
			gap: 0;
			height: var(--bar-height);
			padding: 0;
			background: var(--ink);
		}

		a {
			flex: 1;
			display: flex;
			align-items: center;
			justify-content: center;
			padding: 0;
			color: var(--paper);
		}

		a:hover {
			color: var(--paper);
		}

		a[aria-current='page'] {
			background: var(--paper);
			color: var(--ink);
			box-shadow: inset 0 0 0 4px var(--ink);
		}

		main {
			min-height: 0;
			overflow-y: auto;
			padding-bottom: 0;
		}

		.page {
			display: flex;
			flex-direction: column;
			min-height: 100%;
		}
	}
</style>
