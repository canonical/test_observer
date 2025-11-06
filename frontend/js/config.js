// Configuration for Test Observer Frontend
export const ARTEFACT_TYPES = ["charm", "snap", "deb", "image"];

// API base URL - can be overridden by window.testObserverAPIBaseURI
export const API_BASE_URL = window.testObserverAPIBaseURI || "http://localhost:30000";
