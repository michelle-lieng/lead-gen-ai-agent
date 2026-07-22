// Runtime configuration. In production this file is regenerated at container
// start by entrypoint.sh from the BACKEND_URL env var. In local dev it stays
// empty, so the app falls back to VITE_BACKEND_URL / http://localhost:8000.
window.__BACKEND_URL__ = window.__BACKEND_URL__ || '';
