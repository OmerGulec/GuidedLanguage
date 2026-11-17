<script lang="ts">
	import { goto } from '$app/navigation';

	import { signIn } from '../../api/client';
	import Band from '../../ui/Band.svelte';
	import Content from '../../ui/Content.svelte';
	import Field from '../../ui/Field.svelte';
	import Key from '../../ui/Key.svelte';
	import Notice from '../../ui/Notice.svelte';
	import Stack from '../../ui/Stack.svelte';

	let email = $state('');
	let password = $state('');
	let refused = $state(false);
	let busy = $state(false);

	async function submit(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		busy = true;
		const outcome = await signIn(email, password);
		busy = false;
		if (outcome === 'refused') {
			refused = true;
			return;
		}
		await goto('/');
	}
</script>

<Band title="Sign in" />
<form onsubmit={submit}>
	<Content>
		<Stack narrow>
			{#if refused}
				<Notice>No account has that email and password.</Notice>
			{/if}
			<Field label="Email" type="email" autocomplete="email" bind:value={email} />
			<Field
				label="Password"
				type="password"
				autocomplete="current-password"
				bind:value={password}
			/>
		</Stack>
		{#snippet actions()}
			<Key submit disabled={busy}>Sign in</Key>
		{/snippet}
	</Content>
</form>
