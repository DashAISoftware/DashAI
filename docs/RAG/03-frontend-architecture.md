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

While a turn is in flight, `GenerativeChat` chooses between two status rows:
`RAGChatProgress` when `process.progress` resolves to a known stage, and the
generic waiting bubble otherwise. `RAGChatProgress` maps `transforming`,
`retrieving` (queries joined by `"; "`) and `generating` through
`resolveRAGProgressText`; a null, unknown or malformed payload resolves to null,
so an unrecognized stage can never leave the row blank. The backend resets
`progress` to null when the answer arrives, and the finished branch replaces the
status row.

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

- The five sections are tabs, in the order the pipeline applies them: chunking,
  query transformation, retrieval, model, prompt. Labels come from
  `configuration[key].section_name`, already localized by the backend, so the
  tabs need no translation keys of their own.
- `PillTabs` lays the tabs out on a `repeat(2, 1fr)` grid with its indicator
  hidden: the panel can be 15–40% of the viewport and the labels are
  backend-supplied, so five abreast would wrap or hide half of themselves
  behind a scroll button. The selected tab is marked by its own surface and
  underline instead, and the odd fifth starts a new row.
- **Every tab body stays mounted**, hidden rather than unrendered.
  `GeneratorPicker` reports whether its model can actually run through a
  callback, so a tab the user never opened would leave Save enabled for a model
  that cannot answer.
- One Save sends the whole draft, because edits can be hidden on other tabs and
  a per-tab save would drop them; the endpoint merges the draft over the stored
  parameters. Since tabs hide pending edits, each edited tab gets a dot, a line
  above Save names them, and there is a Discard button.

### Query transformation

The `query_transformation` section is optional: it holds a `{component, params}`
reference, or `null` when the stage is off. `QueryTransformationPicker` owns its
own option loading, so the panel only wires the section.

- The enable switch is disabled while no transformer is registered (no children
  of `BaseQueryTransformation`). Turning it on selects the first technique;
  turning it off writes `null`.
- The technique cards are a `PresetCardList` over the registered transformers.
  A card is matched on `component` alone, because the server fills each
  transformer's `params` with defaults that differ from the empty `{}` a card
  seeds.
- Enabling builds the `{component, params}` reference the PUT expects: the
  generator declared by the transformer schema's `llm_model` placeholder (else
  the first downloaded generator) and the technique's `default` prompt with
  `language: "en"`. Both are seeded because the backend validates them when the
  stage is enabled; everything else is left to the server.
- If the saved component is no longer registered, an info alert names it and
  the remaining technique cards stay available to pick a replacement.
- The Advanced button (disabled while the stage is off) opens
  `QueryTransformationAdvancedModal`, which renders the nested LLM parameters
  from the backend schema through `FormSchema` and offers the technique's
  default prompts.
- The section summary shows the backend's `display_name` when the draft is
  enabled and the "off" label when it is `null`.

`PresetCardList` renders the chunking and retrieval presets, and the query
transformation techniques, as cards in `ComponentSelector`'s idiom — flat
`Paper`, primary border when active, a tick. It does not reuse that component:
the search field, category chips, download controls and viewport-breakpoint
grid it also brings do not apply to a preset recipe, and two columns are
unreadable at this width.

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

## Sources and the retrieval trace

Each answered RAG turn with references or a trace renders `SourcesDisplay`
under the answer (`GenerativeChat.jsx` checks
`message.referenceOutput || message.traceOutput`). It reports the number of
distinct documents, and a **View chunks** button opens `TraceChunksModal` with
that turn's `userMessage`, `trace` (`message.traceOutput`) and `references`
(`message.referenceOutput`).

When the trace has at least one renderable entry, the dialog shows two tabs,
both kept mounted so chunk expansion and query selection survive a tab switch:

- **Chunks** — the final reference chunks grouped by document, with a heading
  that counts chunks and documents and a per-document count. Each card carries
  its provenance ("Found by <retriever> (query N)"), derived from
  `computeProvenance`, plus copy and open-document actions. Bodies longer than
  480 characters collapse behind Show more / Show less, clamped to eight lines.
- **Retriever** — a one-line summary of whether the query was transformed and
  how many candidates survived (kept vs. total, from `collectTraceStats`), a
  selected-chunk panel (or a hint), a per-query selector ("All" plus one chip
  per query when there are several), one `RetrieverTraceTree` per query, and
  the discarded candidates as chips. Clicking a surviving tree chunk
  highlights its final card and fills the selected-chunk panel; clicking a
  discarded one raises a warning snackbar instead.

`RetrieverTraceTree` mirrors `CompositeRetrieverBuilder`'s geometry: composite
nodes in purple, leaves in amber, each node's own chunks indented beneath it
with cross-encoder scores inline and children rendered recursively.

`traceUtils.js` holds the pure derivations (`isQueryTransformed`,
`filterRenderableEntries`, `groupReferencesByDocument`, `collectTraceStats`,
`computeDiscardedRefs`, `computeProvenance`, `getDocumentTitle`,
`resolveChunkLabel`), so the modal only handles layout and interaction.

Legacy answers degrade rather than break. With no trace — `null`, a non-array,
or entries whose `retriever` is not an object — the dialog drops the tabs and
renders a single column of the user message and final chunks. An empty or
absent reference map shows the chunks empty state and leaves the tree rows
non-interactive. The tab and query selection reset only on a close-to-open
transition, not when polling rebuilds the props, and a selection that falls
outside a shrunken trace falls back to the All view.

## Creating a session

`pages/generative/RAG/RAGCreatePage.jsx` is what `/app/generative/rag` renders,
and it asks for a name and a model. Documents are attached from the Data module
once it exists. Only the generation model is sent at creation; the remaining
stages load from the backend's resolved configuration in the session view, with
query transformation starting off.

"Back" on this page leaves RAG for the generative hub, because this page is the
RAG root — there is no longer a menu above it to return to.

## Advanced configuration

In `pages/generative/RAGSession/advanced/`:

- `ChunkingAdvancedModal` / `ChunkingConfigurationStep`
- `RetrieverAdvancedModal` / `RetrieverConfigurationStep`
- `GeneratorAdvancedModal` / `GeneratorConfigurationStep`
- `QueryTransformationAdvancedModal` — the nested LLM parameters, rendered from
  the transformer schema, and the technique's default prompts
- `CompositeRetrieverBuilder` / `RetrieverNodeConfig` — the composite retriever
  tree, with a vertical spine and clickable operation nodes.

## API layer

| Endpoint                                                          | Purpose                                            |
| ----------------------------------------------------------------- | -------------------------------------------------- |
| `/api/v1/generative-session/`                                     | Session CRUD                                       |
| `/api/v1/generative-session/{id}/parameters`                      | Configuration (whole-set)                          |
| `/api/v1/generative-process/`                                     | A chat turn                                        |
| `/api/v1/job/`                                                    | Background jobs (document ingestion)               |
| `/api/v1/rag/sessions/{id}/documents`                             | A session's documents (list, attach, detach)       |
| `/api/v1/documents/{id}`                                          | Document metadata for the preview                  |
| `/api/v1/documents/{id}/content`                                  | Document preview content                           |
| `/api/v1/documents/{id}/outline`                                  | Document preview outline                           |
| `/api/v1/rag/sessions/{id}/configuration`                         | Resolved configuration                             |
| `/api/v1/rag/sessions/{id}/index-status`                          | Whether documents are indexed                      |
| `/api/v1/rag/sessions/{id}/index`                                 | Start or refresh indexing                          |
| `/api/v1/rag/{chunking,retriever}-presets`                        | Preset recipes                                     |
| `/api/v1/component/{name}/children/?recursive=true`               | Child components (retrievers, chunkers, prompts)   |
| `/api/v1/component/?related_component=TextToTextGenerationTask`   | Generator components                               |

## Tests

`yarn test`, using `src/test-utils/renderWithProviders.jsx` — which supplies the
real theme, needed because `PillTabs` reads `theme.palette.ui.box` and a bare
`createTheme()` does not have it.

- `RAGConfigPanel.test.jsx` — five tabs including Transform, an edit made on a
  hidden tab is still reported and saved, one Save carries every section, every
  section stays mounted, and enabling a transformation seeds the
  schema-declared default generator and PUTs the component reference (while
  switching it off sends `null`).
- `QueryTransformationAdvancedModal.test.jsx` — every schema parameter is
  rendered, and only the LLM keys the user actually set are persisted, so a
  fresh ref does not overwrite backend defaults.
- `TraceChunksModal.test.jsx` — the Chunks/Retriever tabs, grouping and
  provenance, the kept-vs-total story strip, query selection, discarded chips,
  chunk expansion, inline scores, and graceful handling of legacy or
  non-array traces, empty references and a trace that shrinks while open.
- `traceUtils.test.js` — the pure helpers: object guards, renderable-entry
  filtering, grouping, candidate stats, discarded refs and provenance.
- `SourcesDisplay.test.jsx` — the document count, and that the View chunks
  button opens `TraceChunksModal` with the turn's trace, references and user
  message.
- `RAGChatProgress.test.jsx` — the transforming, retrieving (queries joined by
  `"; "`) and generating messages, and that a null payload renders nothing.
- `GenerativeChat.test.jsx` — an in-flight RAG message shows the live stage
  line when the payload resolves and falls back to the waiting bubble when it
  does not.
- `PromptEditor.test.jsx` — placeholder validation, that edits are written back
  as a self-contained component ref, and that changing the language leaves the
  template alone.
