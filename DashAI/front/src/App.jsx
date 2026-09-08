import React from "react";

import { BrowserRouter, Outlet, Route, Routes } from "react-router-dom";
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
import RAGDocumentsPage from "./pages/generative/RAG/RAGDocumentsPage";
import RAGHomePage from "./pages/generative/RAG/RAGHomePage";
import RAGPromptsPage from "./pages/generative/RAG/RAGPromptsPage";
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
                    inside session creation. Its own provider scopes the session
                    list to RAG so the shared list stays separate. Route
                    matching is case-insensitive, so the previous
                    /app/generative/RAG/... links keep working. */}
                <Route
                  path="/app/generative/rag"
                  element={
                    <RAGScope>
                      <RAGHomePage />
                    </RAGScope>
                  }
                />
                <Route
                  path="/app/generative/rag/new"
                  element={
                    <RAGScope>
                      <RAGCreatePage />
                    </RAGScope>
                  }
                />
                <Route
                  path="/app/generative/rag/sessions/:id"
                  element={
                    <RAGScope>
                      <RAGSessionPage />
                    </RAGScope>
                  }
                />
                <Route
                  path="/app/generative/rag/documents"
                  element={
                    <RAGScope>
                      <RAGDocumentsPage />
                    </RAGScope>
                  }
                />
                <Route
                  path="/app/generative/rag/prompts"
                  element={
                    <RAGScope>
                      <RAGPromptsPage />
                    </RAGScope>
                  }
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
