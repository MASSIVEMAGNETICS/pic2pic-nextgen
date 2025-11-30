/**
 * Main Page
 * =========
 * Tab-based navigation rendering appropriate content
 */
<script lang="ts">
	import { currentTab, isDevMode } from '$stores';
	import Upload from '$components/Upload.svelte';
	import Presets from '$components/Presets.svelte';
	import Gallery from '$components/Gallery.svelte';
	import Queue from '$components/Queue.svelte';
	import HoloLab from '$components/HoloLab.svelte';
	import DNAEditor from '$components/DNAEditor.svelte';
	import Metrics from '$components/Metrics.svelte';
</script>

<svelte:head>
	<title>pic2pic-nextgen | Holographic Image Reconstruction</title>
</svelte:head>

{#if $currentTab === 'upload'}
	<Upload />
{:else if $currentTab === 'presets'}
	<Presets />
{:else if $currentTab === 'gallery'}
	<Gallery />
{:else if $currentTab === 'queue'}
	<Queue />
{:else if $currentTab === 'holoLab' && $isDevMode}
	<HoloLab />
{:else if $currentTab === 'dnaEditor' && $isDevMode}
	<DNAEditor />
{:else if $currentTab === 'metrics' && $isDevMode}
	<Metrics />
{:else}
	<Upload />
{/if}
