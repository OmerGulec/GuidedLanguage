/** The server's API. Expected outcomes are in the return types; a failed request throws. */

import type { components } from './schema';

type Schemas = components['schemas'];
export type Today = Schemas['Today'];
export type Next = Schemas['Next'];
export type Step = Next['step'];
export type Passage = Schemas['PassageView'];
export type Word = Schemas['WordView'];
export type Grammar = Schemas['GrammarView'];
export type Payload = Schemas['Event']['payload'];

export const SIGNED_OUT = 'signed out';
export type SignedOut = typeof SIGNED_OUT;

const UNAUTHORIZED = 401;
const JSON_HEADERS = { 'Content-Type': 'application/json' };

async function call(path: string, init: RequestInit = {}): Promise<Response | SignedOut> {
	const response = await fetch(path, init);
	if (response.status === UNAUTHORIZED) return SIGNED_OUT;
	if (!response.ok) throw new Error(`${init.method ?? 'GET'} ${path} answered ${response.status}`);
	return response;
}

async function read<T>(path: string): Promise<T | SignedOut> {
	const response = await call(path);
	return response === SIGNED_OUT ? response : ((await response.json()) as T);
}

export async function signIn(email: string, password: string): Promise<'signed in' | 'refused'> {
	const response = await call('/api/session', {
		method: 'POST',
		headers: JSON_HEADERS,
		body: JSON.stringify({ email, password })
	});
	return response === SIGNED_OUT ? 'refused' : 'signed in';
}

export function today(): Promise<Today | SignedOut> {
	return read<Today>('/api/today');
}

export function nextStep(): Promise<Next | SignedOut> {
	return read<Next>('/api/study/next');
}

/** Records what the learner did; returns the event's id, or that the server's clock disagrees. */
export async function record(payload: Payload): Promise<string | 'clock ahead' | SignedOut> {
	const id = crypto.randomUUID();
	const response = await call('/api/events', {
		method: 'POST',
		headers: JSON_HEADERS,
		body: JSON.stringify([{ id, at: new Date().toISOString(), payload }])
	});
	if (response === SIGNED_OUT) return response;

	const received = (await response.json()) as Schemas['Received'];
	return received.refused.length > 0 ? 'clock ahead' : id;
}
