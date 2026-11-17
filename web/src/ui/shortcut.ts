/** A handler for the window's key presses that calls `press` for one key, typed outside a field. */
export function shortcut(key: string, press: () => void): (event: KeyboardEvent) => void {
	return (event) => {
		const typing =
			event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement;
		const plain = !(event.ctrlKey || event.metaKey || event.altKey || event.repeat);
		if (event.key !== key || !plain || typing) return;

		event.preventDefault();
		press();
	};
}

const NAMES: Record<string, string> = { ' ': 'space', Enter: 'enter' };

export function keyName(key: string): string {
	return NAMES[key] ?? key;
}
