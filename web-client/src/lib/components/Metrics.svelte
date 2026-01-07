/**
 * Metrics Component (Dev Mode)
 * ============================
 * System health and performance metrics
 */
<script lang="ts">
	import { systemHealth, wsConnected, requestHealth } from '$stores';
	import { onMount, onDestroy } from 'svelte';

	let refreshInterval: ReturnType<typeof setInterval>;

	function getStatusColor(status: string): string {
		switch (status) {
			case 'healthy':
				return 'text-green-400';
			case 'degraded':
				return 'text-amber-400';
			case 'unhealthy':
				return 'text-red-400';
			case 'recovering':
				return 'text-blue-400';
			default:
				return 'text-gray-400';
		}
	}

	function getDeviceIcon(device: string): string {
		switch (device) {
			case 'cuda':
				return '🎮';
			case 'cpu':
				return '💻';
			case 'mps':
				return '🍎';
			default:
				return '❓';
		}
	}

	onMount(() => {
		requestHealth();
		refreshInterval = setInterval(() => {
			if ($wsConnected) {
				requestHealth();
			}
		}, 5000);
	});

	onDestroy(() => {
		clearInterval(refreshInterval);
	});
</script>

<div class="mx-auto max-w-4xl p-6">
	<div class="mb-6 flex items-center justify-between">
		<h2 class="text-2xl font-semibold">System Metrics</h2>
		<button class="rounded-lg bg-indigo-500/20 px-4 py-2 text-indigo-400 transition-colors hover:bg-indigo-500/30" on:click={requestHealth}>
			Refresh
		</button>
	</div>

	<!-- Connection Status -->
	<div class="glass mb-6 rounded-xl p-4">
		<div class="flex items-center gap-3">
			<div class="h-3 w-3 rounded-full {$wsConnected ? 'bg-green-400' : 'bg-red-400'}"></div>
			<span>WebSocket: {$wsConnected ? 'Connected' : 'Disconnected'}</span>
		</div>
	</div>

	{#if $systemHealth}
		<!-- Health Overview -->
		<div class="mb-6 grid gap-4 md:grid-cols-3">
			<div class="glass rounded-xl p-4">
				<div class="mb-2 text-sm text-gray-400">Status</div>
				<div class="text-2xl font-bold {getStatusColor($systemHealth.status)}">
					{$systemHealth.status.toUpperCase()}
				</div>
			</div>

			<div class="glass rounded-xl p-4">
				<div class="mb-2 text-sm text-gray-400">Device</div>
				<div class="text-2xl font-bold">
					{getDeviceIcon($systemHealth.device_mode)}
					{$systemHealth.device_mode.toUpperCase()}
				</div>
			</div>

			<div class="glass rounded-xl p-4">
				<div class="mb-2 text-sm text-gray-400">Memory Usage</div>
				<div class="text-2xl font-bold">{$systemHealth.memory_usage_mb.toFixed(0)} MB</div>
			</div>
		</div>

		<!-- Detailed Metrics -->
		<div class="glass rounded-xl p-6">
			<h3 class="mb-4 font-medium text-indigo-400">Detailed Status</h3>

			<div class="space-y-3 text-sm">
				{#if $systemHealth.cpu_temp_c}
					<div class="flex justify-between">
						<span class="text-gray-400">CPU Temperature</span>
						<span class="{$systemHealth.cpu_temp_c > 85 ? 'text-red-400' : 'text-gray-300'}">
							{$systemHealth.cpu_temp_c.toFixed(1)}°C
						</span>
					</div>
				{/if}

				<div class="flex justify-between">
					<span class="text-gray-400">Consecutive Failures</span>
					<span class="{$systemHealth.consecutive_failures > 0 ? 'text-amber-400' : 'text-gray-300'}">
						{$systemHealth.consecutive_failures}
					</span>
				</div>

				<div class="flex justify-between">
					<span class="text-gray-400">Message</span>
					<span class="text-gray-300">{$systemHealth.message}</span>
				</div>
			</div>
		</div>

		<!-- Self-Healing Rules -->
		<div class="glass mt-6 rounded-xl p-6">
			<h3 class="mb-4 font-medium text-indigo-400">Self-Healing Rules</h3>
			<ul class="space-y-2 text-sm text-gray-300">
				<li>✓ GPU OOM → Flush memory bank → Retry on CPU</li>
				<li>✓ Process crash → Watchdog restarts within 3s</li>
				<li>✓ Corrupted .holo file → Fractal reconstruction from remaining scales</li>
				<li>✓ High CPU temp (&gt;85°C) → Throttle batch size</li>
				<li>✓ Network drop → Exponential backoff + local queue</li>
				<li>✓ Every 1000 ops → Integrity check (cosine similarity &gt; 0.92)</li>
			</ul>
		</div>
	{:else}
		<div class="glass flex min-h-48 flex-col items-center justify-center rounded-xl p-8">
			<div class="mb-4 animate-pulse text-5xl">📊</div>
			<p class="text-gray-400">Loading system metrics...</p>
		</div>
	{/if}
</div>
