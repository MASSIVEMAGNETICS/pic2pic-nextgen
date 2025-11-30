/**
 * HoloLab Component (Dev Mode)
 * ============================
 * Advanced parameter controls and shard visualization
 */
<script lang="ts">
	import { devParameters, shardActivations, setDevParams, getDevParams } from '$stores';
	import { onMount } from 'svelte';

	let localParams = { ...$devParameters };

	function handleParamChange() {
		setDevParams(localParams);
	}

	function resetParams() {
		localParams = {
			tau_scale_1: 0.1,
			tau_scale_2: 0.2,
			tau_scale_3: 0.3,
			tau_scale_4: 0.4,
			cleanup_k_top: 50,
			binding_temperature: 1.0,
			binding_strength: 0.8,
			cosine_threshold: 0.92
		};
		setDevParams(localParams);
	}

	// Sync with store
	$: localParams = { ...$devParameters };

	onMount(() => {
		getDevParams();
	});
</script>

<div class="mx-auto max-w-6xl p-6">
	<div class="mb-6 flex items-center justify-between">
		<h2 class="text-2xl font-semibold">HoloLab</h2>
		<button class="rounded-lg bg-amber-500/20 px-4 py-2 text-amber-400 transition-colors hover:bg-amber-500/30" on:click={resetParams}>
			Reset to Defaults
		</button>
	</div>

	<div class="grid gap-6 lg:grid-cols-2">
		<!-- Parameter Controls -->
		<div class="glass rounded-xl p-6">
			<h3 class="mb-4 font-medium text-indigo-400">Tau Values (Per Scale)</h3>

			{#each [1, 2, 3, 4] as scale}
				<div class="mb-4">
					<div class="mb-1 flex justify-between text-sm">
						<label for="tau_{scale}">Scale {scale}</label>
						<span class="text-gray-400">{localParams[`tau_scale_${scale}` as keyof typeof localParams]}</span>
					</div>
					<input
						id="tau_{scale}"
						type="range"
						min="0"
						max="1"
						step="0.01"
						bind:value={localParams[`tau_scale_${scale}` as keyof typeof localParams]}
						on:change={handleParamChange}
						class="w-full accent-indigo-500"
					/>
				</div>
			{/each}
		</div>

		<div class="glass rounded-xl p-6">
			<h3 class="mb-4 font-medium text-indigo-400">Binding Parameters</h3>

			<div class="mb-4">
				<div class="mb-1 flex justify-between text-sm">
					<label for="cleanup_k">Cleanup K-Top</label>
					<span class="text-gray-400">{localParams.cleanup_k_top}</span>
				</div>
				<input
					id="cleanup_k"
					type="range"
					min="1"
					max="100"
					bind:value={localParams.cleanup_k_top}
					on:change={handleParamChange}
					class="w-full accent-indigo-500"
				/>
			</div>

			<div class="mb-4">
				<div class="mb-1 flex justify-between text-sm">
					<label for="binding_temp">Binding Temperature</label>
					<span class="text-gray-400">{localParams.binding_temperature.toFixed(2)}</span>
				</div>
				<input
					id="binding_temp"
					type="range"
					min="0.1"
					max="5"
					step="0.1"
					bind:value={localParams.binding_temperature}
					on:change={handleParamChange}
					class="w-full accent-indigo-500"
				/>
			</div>

			<div class="mb-4">
				<div class="mb-1 flex justify-between text-sm">
					<label for="binding_strength">Binding Strength</label>
					<span class="text-gray-400">{localParams.binding_strength.toFixed(2)}</span>
				</div>
				<input
					id="binding_strength"
					type="range"
					min="0"
					max="1"
					step="0.01"
					bind:value={localParams.binding_strength}
					on:change={handleParamChange}
					class="w-full accent-indigo-500"
				/>
			</div>

			<div>
				<div class="mb-1 flex justify-between text-sm">
					<label for="cosine_threshold">Cosine Threshold</label>
					<span class="text-gray-400">{localParams.cosine_threshold.toFixed(2)}</span>
				</div>
				<input
					id="cosine_threshold"
					type="range"
					min="0.5"
					max="1"
					step="0.01"
					bind:value={localParams.cosine_threshold}
					on:change={handleParamChange}
					class="w-full accent-indigo-500"
				/>
			</div>
		</div>
	</div>

	<!-- Shard Activation Visualization -->
	<div class="glass mt-6 rounded-xl p-6">
		<h3 class="mb-4 font-medium text-indigo-400">Shard Activation Heatmap</h3>

		{#if $shardActivations.length === 0}
			<div class="flex h-48 items-center justify-center text-gray-500">
				Process an image to see shard activations
			</div>
		{:else}
			<div class="relative h-64 overflow-hidden rounded-lg bg-black/30">
				{#each $shardActivations as shard (shard.shard_id)}
					<div
						class="absolute h-4 w-4 rounded-full transition-all"
						style="
							left: {shard.coordinates[0] * 4}px;
							top: {shard.coordinates[1] * 4}px;
							background: rgba(99, 102, 241, {shard.activation});
							box-shadow: 0 0 {shard.activation * 20}px rgba(99, 102, 241, {shard.activation});
						"
					></div>
				{/each}
			</div>
			<div class="mt-2 flex justify-between text-xs text-gray-500">
				<span>Active shards: {$shardActivations.length}</span>
				<span>Scale distribution: {[...new Set($shardActivations.map((s) => s.scale))].join(', ')}</span>
			</div>
		{/if}
	</div>
</div>
