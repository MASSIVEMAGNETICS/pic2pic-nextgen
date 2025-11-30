/**
 * Application State Stores
 * ========================
 * Centralized state management for pic2pic-nextgen
 */
import { writable, derived, type Writable } from 'svelte/store';

// ============================================================================
// Types
// ============================================================================

export type UIMode = 'user' | 'dev';

export interface DevParameters {
	tau_scale_1: number;
	tau_scale_2: number;
	tau_scale_3: number;
	tau_scale_4: number;
	cleanup_k_top: number;
	binding_temperature: number;
	binding_strength: number;
	cosine_threshold: number;
}

export interface ProcessingJob {
	id: string;
	status: 'queued' | 'processing' | 'completed' | 'error';
	progress: number;
	mode: string;
	inputUrl?: string;
	resultUrl?: string;
	error?: string;
}

export interface ShardActivation {
	shard_id: number;
	scale: number;
	activation: number;
	coordinates: [number, number];
}

export interface SystemHealth {
	status: 'healthy' | 'degraded' | 'unhealthy' | 'recovering';
	device_mode: 'cuda' | 'cpu' | 'mps';
	memory_usage_mb: number;
	cpu_temp_c: number | null;
	message: string;
}

export interface Preset {
	name: string;
	mode: string;
	description: string;
}

// ============================================================================
// Stores
// ============================================================================

/**
 * UI Mode - switches between user-friendly and dev interfaces
 */
export const uiMode: Writable<UIMode> = writable('user');

/**
 * Dev mode toggle (Ctrl+Shift+D)
 */
export function toggleDevMode(): void {
	uiMode.update((mode) => (mode === 'user' ? 'dev' : 'user'));
}

/**
 * Current processing jobs
 */
export const jobs: Writable<Map<string, ProcessingJob>> = writable(new Map());

/**
 * Add or update a job
 */
export function updateJob(job: ProcessingJob): void {
	jobs.update((map) => {
		map.set(job.id, job);
		return map;
	});
}

/**
 * Remove a job
 */
export function removeJob(id: string): void {
	jobs.update((map) => {
		map.delete(id);
		return map;
	});
}

/**
 * Live shard activations during processing
 */
export const shardActivations: Writable<ShardActivation[]> = writable([]);

/**
 * System health status
 */
export const systemHealth: Writable<SystemHealth | null> = writable(null);

/**
 * Dev parameters (only visible in dev mode)
 */
export const devParameters: Writable<DevParameters> = writable({
	tau_scale_1: 0.1,
	tau_scale_2: 0.2,
	tau_scale_3: 0.3,
	tau_scale_4: 0.4,
	cleanup_k_top: 50,
	binding_temperature: 1.0,
	binding_strength: 0.8,
	cosine_threshold: 0.92
});

/**
 * Available presets
 */
export const presets: Writable<Preset[]> = writable([
	{ name: 'Enhance', mode: 'enhance', description: 'Improve image quality and clarity' },
	{ name: 'Stylize', mode: 'stylize', description: 'Apply artistic style transformation' },
	{ name: 'De-old Photo', mode: 'de-old-photo', description: 'Restore and enhance old photographs' },
	{ name: 'Make Anime', mode: 'make-anime', description: 'Transform to anime/illustration style' }
]);

/**
 * Selected preset mode
 */
export const selectedMode: Writable<string> = writable('enhance');

/**
 * Strength slider value (0-100 for user mode)
 */
export const strengthValue: Writable<number> = writable(75);

/**
 * Current tab
 */
export const currentTab: Writable<string> = writable('upload');

/**
 * WebSocket connection status
 */
export const wsConnected: Writable<boolean> = writable(false);

/**
 * Gallery of processed images
 */
export interface GalleryItem {
	id: string;
	inputUrl: string;
	outputUrl: string;
	mode: string;
	timestamp: Date;
}

export const gallery: Writable<GalleryItem[]> = writable([]);

/**
 * Add item to gallery
 */
export function addToGallery(item: GalleryItem): void {
	gallery.update((items) => [item, ...items].slice(0, 100)); // Keep last 100
}

// ============================================================================
// Derived Stores
// ============================================================================

/**
 * Active jobs (queued or processing)
 */
export const activeJobs = derived(jobs, ($jobs) =>
	Array.from($jobs.values()).filter((j) => j.status === 'queued' || j.status === 'processing')
);

/**
 * Is dev mode active
 */
export const isDevMode = derived(uiMode, ($mode) => $mode === 'dev');

/**
 * Tabs visible in current mode
 */
export const visibleTabs = derived(uiMode, ($mode) => {
	if ($mode === 'dev') {
		return ['upload', 'presets', 'gallery', 'queue', 'holoLab', 'dnaEditor', 'metrics'];
	}
	return ['upload', 'presets', 'gallery', 'queue'];
});
