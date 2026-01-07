/**
 * Gallery Component
 * =================
 * Display processed images
 */
<script lang="ts">
	import { gallery, type GalleryItem } from '$stores';

	let selectedItem: GalleryItem | null = null;

	function openModal(item: GalleryItem) {
		selectedItem = item;
	}

	function closeModal() {
		selectedItem = null;
	}

	function downloadImage(item: GalleryItem) {
		const link = document.createElement('a');
		link.href = item.outputUrl;
		link.download = `pic2pic-${item.id}.png`;
		link.click();
	}
</script>

<div class="mx-auto max-w-6xl p-6">
	<h2 class="mb-6 text-2xl font-semibold">Gallery</h2>

	{#if $gallery.length === 0}
		<div class="glass flex min-h-64 flex-col items-center justify-center rounded-xl p-8">
			<div class="mb-4 text-6xl opacity-50">🖼️</div>
			<p class="text-gray-400">No processed images yet</p>
			<p class="mt-2 text-sm text-gray-500">Upload an image to get started</p>
		</div>
	{:else}
		<div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
			{#each $gallery as item (item.id)}
				<button
					class="glass group relative overflow-hidden rounded-xl transition-all hover:glow"
					on:click={() => openModal(item)}
				>
					<img
						src={item.outputUrl}
						alt="Processed"
						class="aspect-square w-full object-cover transition-transform group-hover:scale-105"
					/>
					<div
						class="absolute inset-0 flex items-end bg-gradient-to-t from-black/60 to-transparent
						       opacity-0 transition-opacity group-hover:opacity-100"
					>
						<div class="p-3">
							<span class="rounded-full bg-indigo-500/50 px-2 py-1 text-xs">
								{item.mode}
							</span>
						</div>
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>

<!-- Modal -->
{#if selectedItem}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
		role="dialog"
		aria-modal="true"
		on:click={closeModal}
		on:keydown={(e) => e.key === 'Escape' && closeModal()}
	>
		<div
			class="glass max-h-[90vh] max-w-4xl overflow-auto rounded-2xl p-6"
			on:click|stopPropagation
			on:keydown|stopPropagation
			role="document"
		>
			<div class="mb-4 flex items-center justify-between">
				<h3 class="text-xl font-semibold">Image Details</h3>
				<button class="text-2xl text-gray-400 hover:text-white" on:click={closeModal}>×</button>
			</div>

			<div class="grid gap-4 md:grid-cols-2">
				<div>
					<p class="mb-2 text-sm text-gray-400">Input</p>
					<img src={selectedItem.inputUrl} alt="Input" class="w-full rounded-lg" />
				</div>
				<div>
					<p class="mb-2 text-sm text-gray-400">Output ({selectedItem.mode})</p>
					<img src={selectedItem.outputUrl} alt="Output" class="w-full rounded-lg" />
				</div>
			</div>

			<div class="mt-4 flex justify-end gap-2">
				<button class="rounded-lg bg-white/10 px-4 py-2 transition-colors hover:bg-white/20" on:click={closeModal}>
					Close
				</button>
				<button
					class="rounded-lg bg-indigo-500 px-4 py-2 transition-colors hover:bg-indigo-600"
					on:click={() => downloadImage(selectedItem!)}
				>
					Download
				</button>
			</div>
		</div>
	</div>
{/if}
