<script lang="ts">
	interface Progress {
		done: number;
		total: number;
		label: string;
	}

	interface Props {
		title: string;
		note?: string;
		/** Takes the place of the rule under the title. */
		progress?: Progress;
	}

	let { title, note, progress }: Props = $props();
</script>

<header class:ruled={progress === undefined}>
	<h1>{title}</h1>
	{#if note !== undefined}<span>{note}</span>{/if}
</header>
{#if progress !== undefined}
	<div
		class="progress"
		role="progressbar"
		aria-label={progress.label}
		aria-valuemin="0"
		aria-valuemax={progress.total}
		aria-valuenow={progress.done}
	>
		<div style:width="{progress.total === 0 ? 0 : (100 * progress.done) / progress.total}%"></div>
	</div>
{/if}

<style>
	header {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		justify-content: space-between;
		gap: var(--space-2);
		margin-top: var(--space-4);
		padding-bottom: var(--space-2);
	}

	.ruled {
		border-bottom: var(--rule-heavy) solid var(--ink);
	}

	h1 {
		margin: 0;
		font-size: var(--type-title);
		font-weight: 700;
		line-height: 1.2;
	}

	span {
		font-size: var(--type-label);
		font-variant-caps: all-small-caps;
		letter-spacing: var(--tracking-label);
	}

	.progress {
		box-sizing: border-box;
		height: 11px;
		border: var(--rule-light) solid var(--ink);
	}

	.progress div {
		height: 100%;
		background: var(--ink);
	}
</style>
