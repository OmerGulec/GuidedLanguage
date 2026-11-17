<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	import {
		nextStep,
		record,
		SIGNED_OUT,
		type Next,
		type Passage as Shown,
		type Payload
	} from '../../api/client';
	import Band from '../../ui/Band.svelte';
	import Content from '../../ui/Content.svelte';
	import Japanese from '../../ui/Japanese.svelte';
	import Key from '../../ui/Key.svelte';
	import Label from '../../ui/Label.svelte';
	import Link from '../../ui/Link.svelte';
	import Notice from '../../ui/Notice.svelte';
	import Passage from '../../ui/Passage.svelte';
	import Stack from '../../ui/Stack.svelte';
	import Text from '../../ui/Text.svelte';

	let next = $state<Next | null>(null);
	let answered = $state(0);
	let shown = $state(false);
	let busy = $state(false);
	let clockAhead = $state(false);
	// The last answer's event, which Undo retracts.
	let last = $state<string | null>(null);

	async function load(): Promise<void> {
		const found = await nextStep();
		if (found === SIGNED_OUT) {
			await goto('/sign-in');
			return;
		}
		next = found;
		shown = false;
	}

	onMount(load);

	async function answer(payload: Payload): Promise<void> {
		busy = true;
		const outcome = await record(payload);
		if (outcome === SIGNED_OUT) {
			await goto('/sign-in');
			return;
		}
		clockAhead = outcome === 'clock ahead';
		if (!clockAhead) {
			last = outcome;
			answered += 1;
		}
		await load();
		busy = false;
	}

	async function undo(): Promise<void> {
		if (last === null) return;
		busy = true;
		const outcome = await record({ kind: 'retracted', event: last });
		if (outcome === SIGNED_OUT) {
			await goto('/sign-in');
			return;
		}
		last = null;
		answered -= 1;
		await load();
		busy = false;
	}

	function marks(passage: Shown, item: string): { start: number; end: number }[] {
		return passage.spans.filter((span) => span.items.includes(item));
	}

	function source(passage: Shown): string {
		return `${passage.source} ${passage.position}`;
	}

	function unhandled(step: never): never {
		throw new Error(`no screen for the step ${JSON.stringify(step)}`);
	}
</script>

<Band
	title="Review"
	note={next === null ? undefined : `${next.left} left`}
	progress={next === null
		? undefined
		: { done: answered, total: answered + next.left, label: 'Done this session' }}
/>

{#if next !== null}
	{@const step = next.step}
	<Content>
		<Stack gap="loose">
			{#if clockAhead}
				<Notice>This device's clock is ahead of the server's, so the answer was not kept.</Notice>
			{/if}

			{#if step.kind === 'card'}
				{@const item = step.item}
				{@const passage = step.passage}
				<Label>{step.rung}{passage === null ? '' : ` · ${source(passage)}`}</Label>
				{#if item.kind === 'word'}
					<Japanese size="word">{step.spelling}</Japanese>
					{#if shown}
						<Stack gap="tight">
							<Japanese size="title">{item.readings.join('、')}</Japanese>
							<Text size="lead">{item.meaning.join('; ')}</Text>
							{#each item.senses as sense, n (n)}
								<Text size="small">{sense.join('; ')}</Text>
							{/each}
						</Stack>
						{#if passage !== null}
							<Stack gap="tight">
								<Passage text={passage.text} marks={marks(passage, item.id)} />
								{#if passage.translation !== null}
									<Text italic>{passage.translation}</Text>
								{/if}
							</Stack>
						{/if}
					{/if}
				{:else}
					{#if passage !== null}
						<Passage text={passage.text} marks={step.marked ? marks(passage, item.id) : []} />
					{:else}
						<Japanese size="word">{item.written ?? item.name}</Japanese>
					{/if}
					{#if shown}
						<Stack gap="tight">
							{#if passage?.translation}
								<Text italic size="lead">{passage.translation}</Text>
							{/if}
							<Text bold>{item.name}</Text>
							{#if item.key !== null}<Text>{item.key}</Text>{/if}
						</Stack>
					{/if}
				{/if}
			{:else if step.kind === 'meeting'}
				{@const item = step.item}
				<Label>New word</Label>
				<Stack gap="tight">
					<Japanese size="word">{step.spelling}</Japanese>
					<Japanese size="title">{item.readings.join('、')}</Japanese>
					<Text size="lead">{item.meaning.join('; ')}</Text>
				</Stack>
				{#if step.passage !== null}
					<Stack gap="tight">
						<Passage text={step.passage.text} marks={marks(step.passage, item.id)} />
						{#if step.passage.translation !== null}
							<Text italic>{step.passage.translation}</Text>
						{/if}
					</Stack>
				{/if}
			{:else if step.kind === 'page'}
				{@const item = step.item}
				<Label>{step.reason === 'new' ? 'New' : 'Again'}</Label>
				{#if item.kind === 'grammar'}
					<Stack gap="tight">
						<Text size="title" bold>{item.name}</Text>
						{#if item.written !== null}<Japanese size="title">{item.written}</Japanese>{/if}
						{#if item.key !== null}<Text size="lead">{item.key}</Text>{/if}
					</Stack>
					{#if item.lesson.trim() !== ''}
						<Text verbatim>{item.lesson}</Text>
					{:else if item.form !== null && item.form.body.trim() !== ''}
						<Text verbatim>{item.form.body}</Text>
					{/if}
				{:else}
					<Stack gap="tight">
						<Japanese size="word">{item.spellings[0] ?? item.readings[0]}</Japanese>
						<Japanese size="title">{item.readings.join('、')}</Japanese>
						<Text size="lead">{item.meaning.join('; ')}</Text>
					</Stack>
				{/if}
			{:else if step.kind === 'done'}
				<Text size="lead">Done for today.</Text>
			{:else}
				{unhandled(step)}
			{/if}
		</Stack>

		{#snippet actions()}
			{#if step.kind === 'card'}
				{#if shown}
					<Key
						shortcut="p"
						disabled={busy}
						onpress={() =>
							answer({
								kind: 'reviewed',
								card: step.card,
								passed: true,
								method: 'self',
								passage: step.passage?.id ?? null
							})}>Pass</Key
					>
					<Key
						quiet
						shortcut="f"
						disabled={busy}
						onpress={() =>
							answer({
								kind: 'reviewed',
								card: step.card,
								passed: false,
								method: 'self',
								passage: step.passage?.id ?? null
							})}>Fail</Key
					>
				{:else}
					<Key shortcut="Enter" onpress={() => (shown = true)}>Show</Key>
				{/if}
			{:else if step.kind === 'meeting'}
				<Key
					shortcut="Enter"
					disabled={busy}
					onpress={() =>
						answer({
							kind: 'introduced',
							item: step.item.id,
							reason: 'new',
							passage: step.passage?.id ?? null
						})}>Continue</Key
				>
			{:else if step.kind === 'page'}
				<Key
					shortcut="Enter"
					disabled={busy}
					onpress={() => answer({ kind: 'introduced', item: step.item.id, reason: step.reason })}
					>Continue</Key
				>
			{:else}
				<Link href="/">Today</Link>
			{/if}
			{#if last !== null}
				<Link shortcut="u" onpress={undo}>Undo</Link>
			{/if}
		{/snippet}
	</Content>
{/if}
