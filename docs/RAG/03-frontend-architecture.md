# Frontend Architecture

## Routes

RAG is a standalone entry point of the generative module, not a step inside
generic session creation. All its routes are declared in
`DashAI/front/src/App.jsx` and wrapped in a `RAGScope`, which provides a
`GenerativeProvider` filtered to `RAGTask` so the shared session list stays
separate. Route matching is case-insensitive, so older `/RAG/...` links keep
working.

| Path                               | Component        | Purpose                         |
| ---------------------------------- | ---------------- | ------------------------------- |
| `/app/generative/rag`              | `RAGCreatePage`  | Create a session (name + model) |
| `/app/generative/rag/sessions/:id` | `RAGSessionPage` | Documents, chat, configuration  |
| `/app/generative/rag/new`          | redirect         | → `/app/generative/rag`         |
| `/app/generative/rag/documents`    | redirect         | → `/app/generative/rag`         |
| `/app/generative/rag/prompts`      | redirect         | → `/app/generative/rag`         |

**The entry point is the creation form.** Picking RAG in the hub used to land on
a menu whose only remaining card was "new session" — a leftover from when
documents and prompts sat beside it — so starting a session took two clicks.
Existing sessions are listed in the left panel of that same screen.

`/app/generative/sessions/:id` is served by `SessionRouter`, which redirects a
`RAGTask` session to its own route. The map from a standalone task to its route
lives in `components/generative/standaloneEntryPoints.js`; the backend decides
*which* tasks are standalone, via each task's `metadata.entry_point`.

The redirects exist because there is no catch-all route: without them a bookmark
of `/rag/new` or of the removed documents and prompts pages would render a blank
page.

## The session view

`pages/generative/RAGSession/RAGSessionPage.jsx` is a three-panel layout:

```
LeftPanel
  GenerativeHubHeader        ← 64px, above the split
  DocumentsBar               ← flex 1 1 55%
  SessionBar showHeader={false}  ← flex 1 1 45%
CenterPanel
  RAGBreadcrumbs             ← page chrome, px:4 pt:4
  GenerativeChat
RightPanel
  RAGConfigPanel
```

Two things about this shape are deliberate:

- **The header sits above the split.** It used to live inside `SessionBar`,
  which RAG mounted in the lower 40% of the column inside an `overflow: auto`
  box — so the way back to the hub rendered half-way down and scrolled out of
  sight. `GenerativeHubHeader` is now its own component, `SessionBar` takes
  `showHeader={false}` here, and both halves may shrink (`1 1 X%`, not `0 0 X%`)
  rather than forcing an outer scroll.
- **The chat is the only centre content.** Opening a session lands straight in
  the conversation, and adjusting retrieval or the model never takes it off
  screen. Reading a document happens in a modal for the same reason.

`RAGBreadcrumbs` is rendered by the page. It used to be rendered by
`GenerativeChat`, which is shared with every generative task and so carried a
`taskName === "RAGTask"` check — and drew the trail inside its own centred
column, lower than the same trail on every other RAG screen.

## The configuration panel

`components/generative/RAG/RAGConfigPanel.jsx`, fed by
`GET /v1/rag/sessions/{id}/configuration` (typed `IRAGConfiguration`).

```
Fixed header:  session name (editable) · stale-index alert · PillTabs
Body:          the active tab — summary line, info tooltip, content
Fixed footer:  context budget · "unsaved changes in …" · Discard · Save
```

- The four sections are tabs, in pipeline order: chunking, retrieval, model,
  prompt. Labels come from `configuration[key].section_name`, already localized
  by the backend, so the tabs need no translation keys of their own.
- `PillTabs` is used `variant="scrollable"`, never `fullWidth`: the panel can be
  15% of the viewport and the labels are backend-supplied, so a fixed-width row
  would wrap.
- **Every tab body stays mounted**, hidden rather than unrendered.
  `GeneratorPicker` reports whether its model can actually run through a
  callback, so a tab the user never opened would leave Save enabled for a model
  that cannot answer.
- One Save sends the whole draft, because
  `PUT /generative-session/{id}/parameters` replaces every parameter at once.
  Since tabs hide pending edits, each edited tab gets a dot, a line above Save
  names them, and there is a Discard button.

`PresetCardList` renders the chunking and retrieval presets as cards in
`ComponentSelector`'s idiom — flat `Paper`, primary border when active, a tick.
It does not reuse that component: the search field, category chips, download
controls and viewport-breakpoint grid it also brings do not apply to a preset
recipe, and two columns are unreadable at this width.

## The prompt

`components/generative/RAG/PromptEditor.jsx` edits the session's own template.
There is no shared prompt library: `rag_prompt` rows are deduplicated by a hash
of their parameters, so two sessions that chose the same template shared one
row, and editing it rewrote the other session's prompt.

The registry's built-in templates (`getDefaultPrompts`) remain, but only to
*seed* the template, and seeding is an explicit choice — the language select
used to overwrite whatever the user had written as a side effect. Nothing is
sent while typing; the panel's Save writes the whole draft.

`HighlightedTextarea`, `PlaceholdersList` and `renderTemplateWithHighlights` are
reused unchanged. A template missing `{chunks}` or `{input}` marks its tab and
blocks Save.

## Creating a session

`pages/generative/RAG/RAGCreatePage.jsx` is what `/app/generative/rag` renders,
and it asks for a name and a model. Documents are uploaded into the session once
it exists, and the other three components come from backend defaults
(`GET /v1/rag/session-defaults` seeds them server-side) that the session view
can change.

"Back" on this page leaves RAG for the generative hub, because this page is the
RAG root — there is no longer a menu above it to return to.

## Advanced configuration

In `pages/generative/RAGSession/advanced/`:

- `ChunkingAdvancedModal` / `ChunkingConfigurationStep`
- `RetrieverAdvancedModal` / `RetrieverConfigurationStep`
- `GeneratorAdvancedModal` / `GeneratorConfigurationStep`
- `CompositeRetrieverBuilder` / `RetrieverNodeConfig` — the composite retriever
  tree, with a vertical spine and clickable operation nodes.

## API layer

| Endpoint                                                | Purpose                     |
| ------------------------------------------------------- | --------------------------- |
| `/api/v1/generative-session/`                           | Session CRUD                |
| `/api/v1/generative-session/{id}/parameters`            | Configuration (whole-set)   |
| `/api/v1/generative-process/`                           | A chat turn                 |
| `/api/v1/job/`                                          | Job dispatch                |
| `/api/v1/document/session/{id}`                         | A session's documents       |
| `/api/v1/document/{id}/view`                            | Document preview (inline)   |
| `/api/v1/document/{id}/extract`                         | On-demand extraction        |
| `/api/v1/document/{id}/extractor`                       | Commit extractor choice     |
| `/api/v1/rag/sessions/{id}/configuration`               | Resolved configuration      |
| `/api/v1/rag/sessions/{id}/index-status`                | Whether documents are indexed |
| `/api/v1/rag/{chunking,retriever}-presets`              | Preset recipes              |
| `/api/v1/component/{name}/children/?include_flags=true` | Child components with flags |

## Tests

`yarn test`, using `src/test-utils/renderWithProviders.jsx` — which supplies the
real theme, needed because `PillTabs` reads `theme.palette.ui.box` and a bare
`createTheme()` does not have it.

- `RAGConfigPanel.test.jsx` — tabs, the dirty/Discard model, that one Save
  carries every section, and that all sections stay mounted.
- `PromptEditor.test.jsx` — placeholder validation, that edits are written back
  as a self-contained component ref, and that changing the language leaves the
  template alone.
