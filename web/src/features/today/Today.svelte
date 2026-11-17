<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	import { SIGNED_OUT, today, type Today } from '../../api/client';
	import Band from '../../ui/Band.svelte';
	import Content from '../../ui/Content.svelte';
	import Key from '../../ui/Key.svelte';
	import Stack from '../../ui/Stack.svelte';
	import Steps from '../../ui/Steps.svelte';
	import Text from '../../ui/Text.svelte';

	let day = $state<Today | null>(null);

	onMount(async () => {
		const found = await today();
		if (found === SIGNED_OUT) {
			await goto('/sign-in');
			return;
		}
		day = found;
	});

	function dated(day: string): string {
		return new Date(`${day}T12:00`).toLocaleDateString('en-GB', {
			weekday: 'long',
			day: 'numeric',
			month: 'long'
		});
	}

	const current = $derived.by(() => {
		if (day === null) return null;
		if (day.reviews > 0) return 0;
		if (day.new > 0) return 1;
		return day.reading > 0 ? 2 : null;
	});
</script>

<Band title="Today" note={day === null ? undefined : dated(day.day)} />
{#if day !== null}
	<Content>
		<Stack gap="loose">
			<Steps
				label="The day's work"
				{current}
				steps={[
					{ name: 'Reviews', amount: day.reviews, unit: 'cards' },
					{ name: 'New', amount: day.new, unit: 'items' },
					{ name: 'Reading', amount: day.reading, unit: 'passages' }
				]}
			/>
			{#if day.reviewed + day.met > 0}
				<Text>So far today: {day.reviewed} cards answered, {day.met} items met.</Text>
			{/if}
			{#if current === 2}
				<Text>Reviews and new items are done for today. Reading opens with the Library, which is not built yet.</Text>
			{:else if current === null}
				<Text>Done for today.</Text>
			{/if}
		</Stack>
		{#snippet actions()}
			{#if current === 0 || current === 1}
				<Key shortcut="Enter" onpress={() => goto('/review')}>Continue</Key>
			{/if}
		{/snippet}
	</Content>
{/if}
