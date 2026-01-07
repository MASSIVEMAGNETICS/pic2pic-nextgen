/**
 * WebSocket Client
 * ================
 * Manages WebSocket connection for real-time communication with backend.
 */
import {
	wsConnected,
	updateJob,
	shardActivations,
	systemHealth,
	devParameters,
	type ProcessingJob,
	type ShardActivation,
	type SystemHealth,
	type DevParameters
} from '$stores';

let ws: WebSocket | null = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 10;
const reconnectDelay = 3000;

/**
 * Connect to WebSocket server
 */
export function connect(url?: string): void {
	if (ws?.readyState === WebSocket.OPEN) return;

	const wsUrl = url || getWebSocketUrl();

	try {
		ws = new WebSocket(wsUrl);

		ws.onopen = () => {
			console.log('WebSocket connected');
			wsConnected.set(true);
			reconnectAttempts = 0;
		};

		ws.onclose = () => {
			console.log('WebSocket disconnected');
			wsConnected.set(false);
			ws = null;

			// Auto-reconnect with exponential backoff
			if (reconnectAttempts < maxReconnectAttempts) {
				reconnectAttempts++;
				const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts - 1);
				console.log(`Reconnecting in ${delay}ms...`);
				setTimeout(() => connect(wsUrl), delay);
			}
		};

		ws.onerror = (error) => {
			console.error('WebSocket error:', error);
		};

		ws.onmessage = (event) => {
			handleMessage(JSON.parse(event.data));
		};
	} catch (error) {
		console.error('WebSocket connection failed:', error);
		wsConnected.set(false);
	}
}

/**
 * Disconnect from WebSocket
 */
export function disconnect(): void {
	if (ws) {
		ws.close();
		ws = null;
	}
}

/**
 * Send message through WebSocket
 */
export function send(message: object): void {
	if (ws?.readyState === WebSocket.OPEN) {
		ws.send(JSON.stringify(message));
	} else {
		console.warn('WebSocket not connected');
	}
}

/**
 * Process an image with live preview
 */
export function processImage(imageData: string, mode: string): void {
	send({
		type: 'process',
		image_data: imageData,
		mode
	});
}

/**
 * Subscribe to job updates
 */
export function subscribeToJob(jobId: string): void {
	send({
		type: 'subscribe',
		job_id: jobId
	});
}

/**
 * Request health status
 */
export function requestHealth(): void {
	send({ type: 'health' });
}

/**
 * Get dev parameters
 */
export function getDevParams(): void {
	send({
		type: 'dev_params',
		action: 'get'
	});
}

/**
 * Set dev parameters
 */
export function setDevParams(params: Partial<DevParameters>): void {
	send({
		type: 'dev_params',
		action: 'set',
		params
	});
}

/**
 * Handle incoming WebSocket message
 */
function handleMessage(message: { type: string; [key: string]: unknown }): void {
	switch (message.type) {
		case 'connected':
			console.log('Connected with ID:', message.connection_id);
			break;

		case 'processing_started':
			updateJob({
				id: message.job_id as string,
				status: 'processing',
				progress: 0,
				mode: message.mode as string
			});
			break;

		case 'progress':
			updateJob({
				id: message.job_id as string,
				status: 'processing',
				progress: message.progress_percent as number,
				mode: ''
			});
			shardActivations.set(message.shard_activations as ShardActivation[]);
			break;

		case 'completed':
			updateJob({
				id: message.job_id as string,
				status: 'completed',
				progress: 100,
				mode: '',
				resultUrl: `data:image/png;base64,${message.result}`
			});
			break;

		case 'error':
			if (message.job_id) {
				updateJob({
					id: message.job_id as string,
					status: 'error',
					progress: 0,
					mode: '',
					error: message.message as string
				});
			}
			console.error('Error:', message.message);
			break;

		case 'health':
			systemHealth.set({
				status: message.status as SystemHealth['status'],
				device_mode: message.device_mode as SystemHealth['device_mode'],
				memory_usage_mb: message.memory_usage_mb as number,
				cpu_temp_c: message.cpu_temp_c as number | null,
				message: message.message as string
			});
			break;

		case 'dev_params':
			if (message.action === 'get') {
				devParameters.set(message.params as DevParameters);
			}
			break;

		case 'pong':
			// Keepalive response
			break;

		default:
			console.log('Unknown message type:', message.type);
	}
}

/**
 * Get WebSocket URL based on current location
 */
function getWebSocketUrl(): string {
	const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	const host = window.location.host;

	// In development, connect to backend directly
	if (import.meta.env.DEV) {
		return 'ws://localhost:8000/ws';
	}

	return `${protocol}//${host}/ws`;
}

// Ping to keep connection alive
setInterval(() => {
	if (ws?.readyState === WebSocket.OPEN) {
		send({ type: 'ping' });
	}
}, 30000);
