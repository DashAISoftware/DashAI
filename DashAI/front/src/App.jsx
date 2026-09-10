import React from "react";

import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";
import { TourRegistryProvider } from "./contexts/TourRegistryContext";
import ModuleThemeWrapper from "./components/ModuleThemeWrapper";

import "./App.css";
import DatasetsPage from "./pages/datasets/Datasets";
import ModelsPage from "./pages/models/Models";
import Home from "./pages/home/Home";
import ResponsiveAppBar from "./components/ResponsiveAppBar";
import PluginsPage from "./pages/plugins/Plugins";
import PipelinesPage from "./pages/pipelines/Pipelines";
import PluginsDetails from "./pages/plugins/components/PluginsDetails";
import Generative from "./pages/generative/Generative";
import { GenerativeProvider } from "./components/generative/GenerativeContext";
import NewPipelineWrapper from "./pages/pipelines/newPipelineWrapper";
import HubContent from "./pages/hub/HubContent";
import HubImportPage from "./pages/hub/HubImportPage";
import JobQueueWidget from "./components/jobs/JobQueueWidget";
import RAGCreatePage from "./pages/generative/RAG/RAGCreatePage";
import RAGSessionPage from "./pages/generative/RAGSession/RAGSessionPage";
import SessionRouter from "./pages/generative/SessionRouter";
import { DatasetsAndNotebooksProvider } from "./components/custom/contexts/DatasetsAndNotebooksContext";
import { DatasetsProvider } from "./contexts/DatasetsContext";
import { ModelsProvider } from "./components/models/ModelsContext";
import { RAG_TASK_NAME } from "./api/rag";

/**
 * Scopes a RAG route to its own session list.
 *
 * The app-level provider serves the shared "create session" flow, which must
 * not see RAG sessions; RAG routes get a provider of their own asking the
 * backend for exactly its task.
 *
 * @param {object} props
 * @param {JSX.Element} props.children - The RAG page to render.
 * @returns {JSX.Element} The scoped subtree.
 */
function RAGScope({ children }) {
  return (
    <GenerativeProvider sessionFilter={{ taskName: RAG_TASK_NAME }}>
      {children}
    </GenerativeProvider>
  );
}

function DataSectionLayout() {
  return (
    <DatasetsAndNotebooksProvider>
      <Outlet />
    </DatasetsAndNotebooksProvider>
  );
}

function App() {
  return (
    <TourRegistryProvider>
      <BrowserRouter
        future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
      >
        <DatasetsProvider>
          <ModelsProvider>
            <GenerativeProvider>
              <ResponsiveAppBar />
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/app" element={<Home />} />
                <Route path="/app/data" element={<DataSectionLayout />}>
                  <Route index element={<DatasetsPage />} />
                  <Route path="datasets/new" element={<DatasetsPage />} />
                  <Route
                    path="datasets/new/:dataloaderName"
                    element={<DatasetsPage />}
                  />
                  <Route path="datasets/:id" element={<DatasetsPage />} />
                  <Route path="notebooks/new" element={<DatasetsPage />} />
                  <Route path="notebooks/:id" element={<DatasetsPage />} />
                  <Route path="hub" element={<HubContent />} />
                  <Route
                    path="hub/import/:datafileId/*"
                    element={<HubImportPage />}
                  />
                  <Route path="hub/:sourceName" element={<HubContent />} />
                </Route>
                <Route path="/app/models" element={<ModelsPage />} />
                <Route
                  path="/app/models/datasets/:id"
                  element={<ModelsPage />}
                />
                <Route
                  path="/app/models/sessions/:id"
                  element={<ModelsPage />}
                />
                <Route
                  path="/app/models/sessions/new/:taskName"
                  element={<ModelsPage />}
                />
                <Route
                  path="/app/models/sessions/:id/model/:runId"
                  element={<ModelsPage />}
                />
                <Route path="/app/generative" element={<Generative />} />
                {/* RAG is an entry point of the Generative module, not a step
                    inside session creation, and the entry point *is* creating a
                    session: picking RAG used to land on a menu whose only card
                    was "new session", so starting one took two clicks. Existing
                    sessions are one click away in the left panel, which its own
                    provider scopes to RAG so the shared list stays separate.
                    Route matching is case-insensitive, so the previous
                    /app/generative/RAG/... links keep working. */}
                <Route
                  path="/app/generative/rag"
                  element={
                    <RAGScope>
                      <RAGCreatePage />
                    </RAGScope>
                  }
                />
                <Route
                  path="/app/generative/rag/new"
                  element={<Navigate to="/app/generative/rag" replace />}
                />
                <Route
                  path="/app/generative/rag/sessions/:id"
                  element={
                    <RAGScope>
                      <RAGSessionPage />
                    </RAGScope>
                  }
                />
                {/* Documents and prompts belong to a session now, so these
                    two pages are gone. There is no catch-all route, so keep the
                    paths redirecting for a release rather than serving a blank
                    page to anyone who bookmarked them. */}
                <Route
                  path="/app/generative/rag/documents"
                  element={<Navigate to="/app/generative/rag" replace />}
                />
                <Route
                  path="/app/generative/rag/prompts"
                  element={<Navigate to="/app/generative/rag" replace />}
                />
                <Route
                  path="/app/generative/sessions/new"
                  element={<Generative />}
                />
                <Route
                  path="/app/generative/sessions/new/:modelName"
                  element={<Generative />}
                />
                <Route
                  path="/app/generative/sessions/:id"
                  element={<SessionRouter />}
                />
                <Route path="/app/pipelines" element={<PipelinesPage />} />
                <Route
                  path="/app/pipelines/new"
                  element={<NewPipelineWrapper />}
                />
                <Route
                  path="/app/pipelines/:pipelineId"
                  element={<NewPipelineWrapper />}
                />
                <Route path="/app/plugins">
                  <Route index element={<PluginsPage />} />
                  <Route path=":category">
                    <Route index element={<PluginsPage />} />
                    <Route path="details/:id" element={<PluginsDetails />} />
                  </Route>
                </Route>
              </Routes>
              <JobQueueWidget />
            </GenerativeProvider>
          </ModelsProvider>
        </DatasetsProvider>
      </BrowserRouter>
    </TourRegistryProvider>
  );
}
export default App;
