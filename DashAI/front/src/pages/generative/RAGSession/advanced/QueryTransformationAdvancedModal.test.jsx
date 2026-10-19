/**
 * The transformation LLM's parameters are rendered from the backend schema,
 * not by hand, and the submit contract has to survive two very different
 * starting states:
 *
 *  - the stage ref already carries params: every carried key plus the edited
 *    ones must be echoed back, or a saved context_window would be lost.
 *  - the stage ref carries none (a freshly enabled picker seeds `{}`): only the
 *    keys the user actually touched may be persisted. Echoing the schema's
 *    placeholder defaults would let a 512 beat the backend's 2048 override.
 *
 * The tests below pin both, plus clearing a field and the legacy hand-rolled
 * transformer fields.
 */

import React from "react";
import { screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// react-markdown ships ESM only and CRA's jest does not transform node_modules,
// so importing any form component pulls in a parse error before a single
// assertion runs. See FormSchemaRenderFields.test.jsx for the same workaround.
jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }) => <span>{children}</span>,
}));

// useFormSchemaStore consumes the snackbar context.
jest.mock("notistack", () => {
  const snackbar = { enqueueSnackbar: jest.fn() };
  return { useSnackbar: () => snackbar };
});

// The form machinery fetches component schemas through getComponents.
jest.mock("../../../../api/component", () => ({
  getComponents: jest.fn(),
}));

// Importing the picker (for resolveLabel) pulls in its API module; stub it so
// no request goes out.
jest.mock("../../../../api/rag", () => ({
  getGeneratorComponents: jest.fn(),
  getQueryTransformationComponents: jest.fn(),
  getQueryTransformationPrompts: jest.fn(),
}));

import { renderWithProviders } from "../../../../test-utils/renderWithProviders";
import QueryTransformationAdvancedModal from "./QueryTransformationAdvancedModal";

const componentApi = require("../../../../api/component");

/** GGUF-like schema the components API ships for a generator. */
const STUB_SCHEMA = {
  properties: {
    max_tokens: {
      type: "integer",
      placeholder: 100,
      title: "Max tokens",
    },
    temperature: {
      type: "number",
      placeholder: 0.7,
      title: "Temperature",
    },
    frequency_penalty: {
      type: "number",
      placeholder: 0.1,
      title: "Frequency penalty",
    },
    context_window: {
      type: "integer",
      placeholder: 512,
      title: "Context window",
    },
    device: {
      type: "string",
      enum: ["CPU", "GPU"],
      placeholder: "CPU",
      title: "Device",
    },
  },
};

/** State A: a saved ref that already carries a chosen context_window. */
const CARRIED_MODEL = {
  component: "LLMQueryRewriter",
  params: {
    llm_model: {
      component: "StubLLM",
      params: { context_window: 4096 },
    },
  },
};

/** State B: a freshly enabled stage, seeded with an empty params map. */
const FRESH_MODEL = {
  component: "LLMQueryRewriter",
  params: {
    llm_model: { component: "StubLLM", params: {} },
  },
};

const GENERATORS = [
  {
    name: "StubLLM",
    display_name: "Stub LLM",
    description: "",
    schema: STUB_SCHEMA,
  },
  {
    name: "OtherLLM",
    display_name: "Other LLM",
    description: "",
    schema: STUB_SCHEMA,
  },
];

/** Renders the modal with the transformation LLM preselected. */
function renderModal(overrides = {}) {
  const setModel = jest.fn();
  const onClose = jest.fn();
  renderWithProviders(
    <QueryTransformationAdvancedModal
      open
      onClose={onClose}
      model={CARRIED_MODEL}
      setModel={setModel}
      technique="rewriting"
      generators={GENERATORS}
      prompts={[]}
      {...overrides}
    />,
  );
  return { setModel, onClose };
}

/** Lets the inputs' 300ms debounce fire before a submit is asserted. */
const flushDebounce = () =>
  act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 350));
  });

/** The params the modal hands to setModel on Done. */
function sentParams(setModel) {
  return setModel.mock.calls[0][0].params.llm_model;
}

beforeEach(() => {
  jest.clearAllMocks();
  componentApi.getComponents.mockResolvedValue({
    name: "StubLLM",
    schema: STUB_SCHEMA,
  });
});

test("renders every schema parameter, not a single hand-rolled field", async () => {
  renderModal();

  // The carried value shows as soon as the form mounts; the schema's own
  // placeholder defaults land a beat later, when useSchema resolves.
  expect(await screen.findByLabelText("Context window")).toHaveValue(4096);
  await waitFor(() =>
    expect(screen.getByLabelText("Max tokens")).toHaveValue(100),
  );
  expect(screen.getByLabelText("Temperature")).toHaveValue(0.7);
  expect(screen.getByLabelText("Frequency penalty")).toHaveValue(0.1);
  expect(screen.getByRole("combobox", { name: "Device" })).toHaveTextContent(
    "CPU",
  );
});

test("editing a carried ref echoes the carried keys plus the edit", async () => {
  const { setModel } = renderModal();
  const temperature = await screen.findByLabelText("Temperature");

  await userEvent.clear(temperature);
  await userEvent.type(temperature, "0.5");
  await flushDebounce();
  await userEvent.click(screen.getByRole("button", { name: "Done" }));

  expect(setModel).toHaveBeenCalledTimes(1);
  expect(sentParams(setModel)).toEqual({
    component: "StubLLM",
    params: { context_window: 4096, temperature: 0.5 },
  });
});

test("a fresh ref with no edits persists no params", async () => {
  const { setModel } = renderModal({ model: FRESH_MODEL });

  expect(await screen.findByLabelText("Context window")).toHaveValue(512);
  await userEvent.click(screen.getByRole("button", { name: "Done" }));

  expect(setModel).toHaveBeenCalledTimes(1);
  expect(sentParams(setModel)).toEqual({
    component: "StubLLM",
    params: {},
  });
  expect("context_window" in sentParams(setModel).params).toBe(false);
});

test("a fresh ref persists only the edited key, leaving the rest to the backend", async () => {
  const { setModel } = renderModal({ model: FRESH_MODEL });
  const temperature = await screen.findByLabelText("Temperature");

  await userEvent.clear(temperature);
  await userEvent.type(temperature, "0.5");
  await flushDebounce();
  await userEvent.click(screen.getByRole("button", { name: "Done" }));

  expect(sentParams(setModel).params).toEqual({ temperature: 0.5 });
});

test("an explicit context_window on a fresh ref wins over the backend default", async () => {
  const { setModel } = renderModal({ model: FRESH_MODEL });
  const contextWindow = await screen.findByLabelText("Context window");

  await userEvent.clear(contextWindow);
  await userEvent.type(contextWindow, "3000");
  await flushDebounce();
  await userEvent.click(screen.getByRole("button", { name: "Done" }));

  expect(sentParams(setModel).params).toEqual({ context_window: 3000 });
});

test("clearing a carried context_window drops it and keeps the other carried keys", async () => {
  const model = {
    component: "LLMQueryRewriter",
    params: {
      llm_model: {
        component: "StubLLM",
        params: { context_window: 4096, temperature: 0.5 },
      },
    },
  };
  const { setModel } = renderModal({ model });
  const contextWindow = await screen.findByLabelText("Context window");

  await userEvent.clear(contextWindow);
  await flushDebounce();
  await userEvent.click(screen.getByRole("button", { name: "Done" }));

  expect(sentParams(setModel).params).toEqual({ temperature: 0.5 });
});

test("keeps the transformer's own fields flowing to Done", async () => {
  const model = {
    component: "LLMQueryRewriter",
    params: {
      llm_model: { component: "StubLLM", params: {} },
      history_window: 2,
    },
  };
  const { setModel } = renderModal({ model });
  const historyWindow = await screen.findByLabelText("History window");

  await userEvent.clear(historyWindow);
  await userEvent.type(historyWindow, "5");
  await userEvent.click(screen.getByRole("button", { name: "Done" }));

  expect(setModel.mock.calls[0][0].params.history_window).toBe(5);
});

test("switching the LLM resets its params to an empty map", async () => {
  const { setModel } = renderModal();

  await screen.findByLabelText("Context window");
  await userEvent.click(
    screen.getByRole("combobox", { name: "Language model" }),
  );
  await userEvent.click(screen.getByRole("option", { name: "Other LLM" }));
  await userEvent.click(screen.getByRole("button", { name: "Done" }));

  expect(sentParams(setModel)).toEqual({
    component: "OtherLLM",
    params: {},
  });
});

test("reopening with an emptied ref re-seeds the emission mode", async () => {
  const setModel = jest.fn();
  const props = (model) => ({
    open: true,
    onClose: jest.fn(),
    model,
    setModel,
    technique: "rewriting",
    generators: GENERATORS,
    prompts: [],
  });
  const view = renderWithProviders(
    <QueryTransformationAdvancedModal {...props(CARRIED_MODEL)} />,
  );
  await screen.findByLabelText("Context window");

  // The session was saved carrying nothing, so the next open must forget the
  // earlier carried baseline: a later edit otherwise echoes stale keys.
  view.rerender(<QueryTransformationAdvancedModal {...props(FRESH_MODEL)} />);
  await flushDebounce();

  const temperature = screen.getByLabelText("Temperature");
  await userEvent.clear(temperature);
  await userEvent.type(temperature, "1.5");
  await flushDebounce();
  await userEvent.click(screen.getByRole("button", { name: "Done" }));

  expect(setModel).toHaveBeenCalledTimes(1);
  expect(sentParams(setModel).params).toEqual({ temperature: 1.5 });
});
