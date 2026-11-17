<script lang="ts">
	interface Mark {
		start: number;
		end: number;
	}

	interface Props {
		text: string;
		/** Where the item being studied stands in the text. */
		marks?: Mark[];
	}

	let { text, marks = [] }: Props = $props();

	interface Run {
		text: string;
		marked: boolean;
	}

	const runs = $derived.by(() => {
		const found: Run[] = [];
		let reached = 0;
		for (const mark of [...marks].sort((a, b) => a.start - b.start)) {
			if (mark.start < reached) continue;
			if (mark.start > reached) found.push({ text: text.slice(reached, mark.start), marked: false });
			found.push({ text: text.slice(mark.start, mark.end), marked: true });
			reached = mark.end;
		}
		if (reached < text.length) found.push({ text: text.slice(reached), marked: false });
		return found;
	});
</script>

<p lang="ja">
	{#each runs as run, n (n)}{#if run.marked}<mark>{run.text}</mark>{:else}{run.text}{/if}{/each}
</p>

<style>
	p {
		margin: 0;
		font-family: var(--mincho);
		font-size: var(--type-sentence);
		line-height: 1.5;
	}

	mark {
		background: none;
		color: inherit;
		border-bottom: var(--rule-heavy) solid var(--ink);
	}
</style>
