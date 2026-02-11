<script>
  import { Router, Route } from 'svelte-routing';
  import { BASE_PATH } from './config';
  import Navbar from './components/Navbar.svelte';
  import Dashboard from './views/Dashboard.svelte';
  import ArtefactPage from './views/ArtefactPage.svelte';
  import TestResultsSearchPage from './views/TestResultsSearchPage.svelte';
  import IssuesPage from './views/IssuesPage.svelte';
  import IssuePage from './views/IssuePage.svelte';

  export let url = '';
</script>

<div id="app">
  <Router {url} basepath={BASE_PATH.slice(0, -1)}>
    <Navbar />
    <main>
      <div class="content-container">
        <Route path="/" component={()=> Dashboard} family="snap" />
        <Route path="/snaps" let:params>
          <Dashboard family="snap" />
        </Route>
        <Route path="/snaps/:artefactId" component={ArtefactPage} />
        <Route path="/debs" let:params>
          <Dashboard family="deb" />
        </Route>
        <Route path="/debs/:artefactId" component={ArtefactPage} />
        <Route path="/charms" let:params>
          <Dashboard family="charm" />
        </Route>
        <Route path="/charms/:artefactId" component={ArtefactPage} />
        <Route path="/images" let:params>
          <Dashboard family="image" />
        </Route>
        <Route path="/images/:artefactId" component={ArtefactPage} />
        <Route path="/test-results" component={TestResultsSearchPage} />
        <Route path="/issues" component={IssuesPage} />
        <Route path="/issues/:issueId" component={IssuePage} />
      </div>
    </main>
  </Router>
</div>

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: Ubuntu, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Cantarell, sans-serif;
    line-height: 1.6;
    color: #111;
    background: #fff;
  }

  #app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  main {
    flex: 1;
    display: flex;
    justify-content: center;
  }

  .content-container {
    width: 100%;
    max-width: 1780px;
    padding: 0 24px;
  }
</style>
