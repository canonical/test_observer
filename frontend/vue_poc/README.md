# Test Observer - Vue.js rewrite POC

## About the directory structure

This is intentionally hosted outside of the frontend/ directory for the sake of
reducing rebuild times.  The existing Dockerfile does a copy of the whole
frontend/ directory prior to the time-consuming Flutter build; the vue.js builds
should be relatively fast in comparison, and if only vue.js sources are updated,
we shouldn't re-trigger all of the Flutter stuff.
