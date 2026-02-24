## Plan: Nuxt 3 Migration - Phase 1 (Scaffold & Home)

We will establish a parallel Vue 3.5 + Nuxt application served from `/vue_poc/` within the existing Docker container. This first iteration focuses on the project structure, build pipeline integration, and a functional Home Page.

**Steps**

1.  **Project Initialization**
    *   Create `frontend/vue_poc/` directory.
    *   Manually scaffold `package.json`, `nuxt.config.ts`, and `app.vue` with correct dependencies (Vue 3.5, Nuxt 3, Pinia).
    *   Configure `nuxt.config.ts` with `app: { baseURL: '/vue_poc/' }` to support the subpath.

2.  **Agent Workflow: Analysis & Design**
    *   **Archaeologist**: Analyze `frontend/lib/main.dart` and `scaffold.dart` to extract the application shell (navigation, header, theme) and home page logic.
    *   **Architect**: Design the Nuxt directory structure (`layouts/default.vue`, `pages/index.vue`), choosing appropriate libraries (e.g., Tailwind or a custom CSS framework to match Yaru).
    *   **Builder**: Implement the `default` layout and `index` page, including a basic API client (using `useFetch`) to prove backend connectivity.

3.  **Docker & Nginx Integration**
    *   Update [frontend/Dockerfile](frontend/Dockerfile) to include a Node.js build stage that compiles the Nuxt app.
    *   Update [frontend/nginx.conf](frontend/nginx.conf) to serve the generated static files from `/vue_poc/`.
    *   Ensure the build process handles the `APT_PROXY` correctly for `npm install`.

4.  **Verification**
    *   Build the container: `docker build .` (or verify via dry-run).
    *   Check that `http://localhost:8080/vue_poc/` loads the new app.
    *   Check that `http://localhost:8080/` still loads the Flutter app.

**Decisions**
-   **Manual Scaffolding**: We will create files manually instead of using `nuxi init` to ensure control over dependencies and avoid potential network/interactive shell issues.
-   **Build Strategy**: We will use `nuxt generate` (SSG) to create static files that Nginx can serve easily, rather than running a Node server side-by-side.

**Verification**
To verify the plan, we will inspect the generated `frontend/vue_poc` files and the modified `Dockerfile`.
