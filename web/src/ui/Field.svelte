<script lang="ts">
	interface Props {
		label: string;
		value: string;
		type?: 'text' | 'email' | 'password';
		autocomplete?: 'email' | 'current-password';
	}

	let { label, value = $bindable(), type = 'text', autocomplete }: Props = $props();
</script>

<label>
	<span>{label}</span>
	<input {type} {autocomplete} required bind:value />
</label>

<style>
	label {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	span {
		font-size: var(--type-label);
		font-variant-caps: all-small-caps;
		letter-spacing: var(--tracking-label);
	}

	input {
		box-sizing: border-box;
		width: 100%;
		min-height: var(--tap-height);
		padding: 0 var(--space-3);
		border: var(--rule-light) solid var(--ink);
		border-radius: 0;
		background: var(--paper);
		color: var(--ink);
		font-family: var(--serif);
		font-size: var(--type-body);
	}

	input:focus-visible {
		outline: 2px solid var(--ink);
		outline-offset: 2px;
	}
</style>
