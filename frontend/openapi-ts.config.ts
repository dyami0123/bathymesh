import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
    input: '../backend/openapi.json', // sign up at app.heyapi.dev
    output: 'src/client',
});