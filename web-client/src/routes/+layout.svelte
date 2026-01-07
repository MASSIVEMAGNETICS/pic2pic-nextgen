/**
 * Root Layout
 * ===========
 * Main application layout with navigation
 */
<script lang="ts">
	import '../app.css';
	import Navigation from '$components/Navigation.svelte';
	import { connect } from '$utils/websocket';
	import { onMount } from 'svelte';

	onMount(() => {
		// Connect to WebSocket on mount
		connect();
	});
</script>

<div class="min-h-screen bg-[var(--color-surface)]">
	<Navigation />
	<main>
		<slot />
	</main>
</div>
