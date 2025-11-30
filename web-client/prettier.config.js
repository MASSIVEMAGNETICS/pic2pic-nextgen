export default {
	plugins: ['prettier-plugin-svelte'],
	overrides: [{ files: '*.svelte', options: { parser: 'svelte' } }],
	singleQuote: true,
	trailingComma: 'none',
	printWidth: 120,
	useTabs: true
};
