/**
 * Presets Component
 * =================
 * Style preset carousel with strength slider
 */
<script lang="ts">
	import { presets, selectedMode, strengthValue, isDevMode } from '$stores';

	const modeIcons: Record<string, string> = {
		enhance: '✨',
		stylize: '🎨',
		'de-old-photo': '📸',
		'make-anime': '🎌'
	};
</script>

<div class="mx-auto max-w-4xl p-6">
	<h2 class="mb-6 text-2xl font-semibold">Select Preset</h2>

	<!-- Preset Cards -->
	<div class="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
		{#each $presets as preset}
			<button
				class="glass rounded-xl p-4 text-left transition-all
				       {$selectedMode === preset.mode ? 'gradient-border glow' : 'hover:border-white/20'}"
				on:click={() => selectedMode.set(preset.mode)}
			>
				<div class="mb-2 text-3xl">{modeIcons[preset.mode] || '🔮'}</div>
				<h3 class="mb-1 font-medium">{preset.name}</h3>
				<p class="text-xs text-gray-400">{preset.description}</p>
			</button>
		{/each}
	</div>

	<!-- Strength Slider (User Mode) -->
	{#if !$isDevMode}
		<div class="glass rounded-xl p-6">
			<div class="mb-4 flex items-center justify-between">
				<label for="strength" class="font-medium">Strength</label>
				<span class="text-indigo-400">{$strengthValue}%</span>
			</div>

			<input
				id="strength"
				type="range"
				min="0"
				max="100"
				bind:value={$strengthValue}
				class="w-full accent-indigo-500"
			/>

			<div class="mt-2 flex justify-between text-xs text-gray-500">
				<span>Subtle</span>
				<span>Strong</span>
			</div>
		</div>
	{/if}

	<!-- Preview with selected preset -->
	<div class="mt-8 text-center">
		<p class="text-gray-400">
			Selected: <span class="font-medium text-indigo-400">
				{$presets.find((p) => p.mode === $selectedMode)?.name || 'None'}
			</span>
		</p>
	</div>
</div>
