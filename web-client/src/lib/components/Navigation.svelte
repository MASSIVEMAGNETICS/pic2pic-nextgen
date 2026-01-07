/**
 * Navigation Component
 * ====================
 * Tab navigation with dev mode support
 */
<script lang="ts">
	import { currentTab, visibleTabs, uiMode, toggleDevMode } from '$stores';

	const tabLabels: Record<string, string> = {
		upload: 'Upload',
		presets: 'Presets',
		gallery: 'Gallery',
		queue: 'Queue',
		holoLab: 'HoloLab',
		dnaEditor: 'DNA Editor',
		metrics: 'Metrics'
	};

	function handleKeydown(event: KeyboardEvent) {
		// Ctrl+Shift+D toggles dev mode
		if (event.ctrlKey && event.shiftKey && event.key === 'D') {
			event.preventDefault();
			toggleDevMode();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<nav class="glass sticky top-0 z-50 border-b border-white/10">
	<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
		<div class="flex items-center gap-3">
			<h1 class="bg-gradient-to-r from-indigo-500 to-cyan-400 bg-clip-text text-xl font-bold text-transparent">
				pic2pic-nextgen
			</h1>
			{#if $uiMode === 'dev'}
				<span class="rounded-full bg-amber-500/20 px-2 py-0.5 text-xs text-amber-400">
					DEV MODE
				</span>
			{/if}
		</div>

		<div class="flex gap-1">
			{#each $visibleTabs as tab}
				<button
					class="rounded-lg px-4 py-2 text-sm font-medium transition-all
					       {$currentTab === tab
						? 'bg-indigo-500/20 text-indigo-400'
						: 'text-gray-400 hover:bg-white/5 hover:text-white'}"
					on:click={() => currentTab.set(tab)}
				>
					{tabLabels[tab]}
				</button>
			{/each}
		</div>

		<div class="text-xs text-gray-500">
			<span title="Press Ctrl+Shift+D to toggle">v2.0.0</span>
		</div>
	</div>
</nav>
