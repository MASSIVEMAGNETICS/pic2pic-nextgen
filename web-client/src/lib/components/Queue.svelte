/**
 * Queue Component
 * ===============
 * Processing queue with progress tracking
 */
<script lang="ts">
	import { jobs, activeJobs, removeJob } from '$stores';

	function getStatusColor(status: string): string {
		switch (status) {
			case 'queued':
				return 'bg-amber-500/20 text-amber-400';
			case 'processing':
				return 'bg-blue-500/20 text-blue-400';
			case 'completed':
				return 'bg-green-500/20 text-green-400';
			case 'error':
				return 'bg-red-500/20 text-red-400';
			default:
				return 'bg-gray-500/20 text-gray-400';
		}
	}
</script>

<div class="mx-auto max-w-4xl p-6">
	<h2 class="mb-6 text-2xl font-semibold">Processing Queue</h2>

	<!-- Active Jobs Count -->
	<div class="mb-6 flex gap-4">
		<div class="glass flex-1 rounded-xl p-4 text-center">
			<div class="text-3xl font-bold text-indigo-400">{$activeJobs.length}</div>
			<div class="text-sm text-gray-400">Active Jobs</div>
		</div>
		<div class="glass flex-1 rounded-xl p-4 text-center">
			<div class="text-3xl font-bold text-green-400">
				{Array.from($jobs.values()).filter((j) => j.status === 'completed').length}
			</div>
			<div class="text-sm text-gray-400">Completed</div>
		</div>
	</div>

	<!-- Job List -->
	{#if $jobs.size === 0}
		<div class="glass flex min-h-48 flex-col items-center justify-center rounded-xl p-8">
			<div class="mb-4 text-5xl opacity-50">📋</div>
			<p class="text-gray-400">No jobs in queue</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each Array.from($jobs.values()) as job (job.id)}
				<div class="glass rounded-xl p-4">
					<div class="mb-2 flex items-center justify-between">
						<div class="flex items-center gap-3">
							<span class="font-mono text-sm text-gray-500">
								{job.id.slice(0, 8)}...
							</span>
							<span class="rounded-full px-2 py-1 text-xs {getStatusColor(job.status)}">
								{job.status}
							</span>
							{#if job.mode}
								<span class="text-sm text-gray-400">{job.mode}</span>
							{/if}
						</div>
						<button
							class="text-gray-500 hover:text-red-400"
							on:click={() => removeJob(job.id)}
							title="Remove"
						>
							×
						</button>
					</div>

					{#if job.status === 'processing'}
						<div class="h-2 overflow-hidden rounded-full bg-white/10">
							<div
								class="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all"
								style="width: {job.progress}%"
							></div>
						</div>
						<div class="mt-1 text-right text-xs text-gray-500">
							{job.progress.toFixed(1)}%
						</div>
					{/if}

					{#if job.error}
						<p class="mt-2 text-sm text-red-400">{job.error}</p>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
