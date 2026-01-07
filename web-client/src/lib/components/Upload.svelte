/**
 * Image Upload Component
 * ======================
 * Drag & drop or click to upload images
 */
<script lang="ts">
	import { processImage } from '$utils/websocket';
	import { selectedMode, jobs } from '$stores';
	import { onMount } from 'svelte';

	let isDragging = false;
	let inputElement: HTMLInputElement;
	let previewUrl: string | null = null;
	let currentJobId: string | null = null;
	let resultUrl: string | null = null;
	let errorMessage: string | null = null;

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		isDragging = true;
	}

	function handleDragLeave() {
		isDragging = false;
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		isDragging = false;

		const files = event.dataTransfer?.files;
		if (files && files.length > 0) {
			handleFile(files[0]);
		}
	}

	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		const files = target.files;
		if (files && files.length > 0) {
			handleFile(files[0]);
		}
	}

	function handleFile(file: File) {
		errorMessage = null;
		if (!file.type.startsWith('image/')) {
			errorMessage = 'Please upload an image file (PNG, JPG, WebP)';
			return;
		}

		const reader = new FileReader();
		reader.onload = (e) => {
			const dataUrl = e.target?.result as string;
			previewUrl = dataUrl;
			resultUrl = null;

			// Extract base64 data (remove data:image/...;base64, prefix)
			const base64Data = dataUrl.split(',')[1];

			// Process via WebSocket
			processImage(base64Data, $selectedMode);
		};
		reader.readAsDataURL(file);
	}

	function handlePaste(event: ClipboardEvent) {
		const items = event.clipboardData?.items;
		if (!items) return;

		for (const item of items) {
			if (item.type.startsWith('image/')) {
				const blob = item.getAsFile();
				if (blob) {
					handleFile(blob);
				}
				break;
			}
		}
	}

	// Watch for job completion
	$: {
		if (currentJobId) {
			const job = $jobs.get(currentJobId);
			if (job?.status === 'completed' && job.resultUrl) {
				resultUrl = job.resultUrl;
			}
		}
	}

	// Track the latest job
	$: {
		const jobArray = Array.from($jobs.values());
		const latest = jobArray[jobArray.length - 1];
		if (latest) {
			currentJobId = latest.id;
		}
	}

	onMount(() => {
		// Listen for paste events
		document.addEventListener('paste', handlePaste);
		return () => document.removeEventListener('paste', handlePaste);
	});
</script>

<div class="mx-auto max-w-4xl p-6">
	<h2 class="mb-6 text-2xl font-semibold">Upload Image</h2>

	<!-- Error Message -->
	{#if errorMessage}
		<div class="mb-4 flex items-center justify-between rounded-lg bg-red-500/20 px-4 py-3 text-red-400">
			<span>{errorMessage}</span>
			<button class="ml-4 text-xl hover:text-red-300" on:click={() => (errorMessage = null)}>×</button>
		</div>
	{/if}

	<!-- Upload Area -->
	<div
		class="gradient-border mb-6 flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-2xl p-8 transition-all
		       {isDragging ? 'glow scale-[1.02]' : 'hover:glow'}"
		role="button"
		tabindex="0"
		on:click={() => inputElement.click()}
		on:keypress={(e) => e.key === 'Enter' && inputElement.click()}
		on:dragover={handleDragOver}
		on:dragleave={handleDragLeave}
		on:drop={handleDrop}
	>
		{#if previewUrl}
			<img src={previewUrl} alt="Preview" class="mb-4 max-h-48 rounded-lg object-contain" />
		{:else}
			<div class="mb-4 text-6xl opacity-50">📁</div>
		{/if}

		<p class="text-lg text-gray-300">
			{#if isDragging}
				Drop image here
			{:else}
				Drag & drop an image, paste from clipboard, or click to browse
			{/if}
		</p>
		<p class="mt-2 text-sm text-gray-500">Supports PNG, JPG, WebP</p>
	</div>

	<input
		bind:this={inputElement}
		type="file"
		accept="image/*"
		class="hidden"
		on:change={handleFileSelect}
	/>

	<!-- Preview Section -->
	{#if previewUrl || resultUrl}
		<div class="grid grid-cols-2 gap-6">
			<div class="glass rounded-xl p-4">
				<h3 class="mb-3 text-sm font-medium text-gray-400">Input</h3>
				{#if previewUrl}
					<img src={previewUrl} alt="Input" class="w-full rounded-lg" />
				{/if}
			</div>

			<div class="glass rounded-xl p-4">
				<h3 class="mb-3 text-sm font-medium text-gray-400">Output</h3>
				{#if resultUrl}
					<img src={resultUrl} alt="Output" class="w-full rounded-lg" />
				{:else}
					<div class="flex aspect-video items-center justify-center rounded-lg bg-black/20">
						<div class="animate-pulse text-gray-500">Processing...</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
