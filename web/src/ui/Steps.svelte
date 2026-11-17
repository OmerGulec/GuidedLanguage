<script lang="ts">
	interface Step {
		name: string;
		amount: number;
		unit: string;
	}

	interface Props {
		label: string;
		steps: Step[];
		/** The step the learner is on, counted from zero; null once all are done. */
		current: number | null;
	}

	let { label, steps, current }: Props = $props();
</script>

<ol aria-label={label}>
	{#each steps as step, n (step.name)}
		<li aria-current={n === current ? 'step' : undefined}>
			<span class="number">{n + 1}</span>
			<span class="name">{step.name}</span>
			<span><b>{step.amount}</b> <span class="unit">{step.unit}</span></span>
		</li>
	{/each}
</ol>

<style>
	ol {
		box-sizing: border-box;
		width: 100%;
		max-width: 34rem;
		margin: 0;
		padding: var(--space-2) 0;
		border-top: var(--rule) solid var(--ink);
		border-bottom: var(--rule) solid var(--ink);
		list-style: none;
	}

	li {
		display: grid;
		grid-template-columns: 2rem 1fr auto;
		align-items: baseline;
		gap: var(--space-3);
		padding: var(--space-2) var(--space-3);
	}

	.number {
		font-size: var(--type-label);
	}

	.name {
		font-size: var(--type-lead);
	}

	[aria-current] .name {
		font-weight: 700;
	}

	b {
		font-size: var(--type-figure);
	}

	.unit {
		font-size: var(--type-label);
		font-variant-caps: all-small-caps;
		letter-spacing: var(--tracking-label);
	}
</style>
