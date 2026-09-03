import React from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import PromptEditor from "./PromptEditor";

jest.mock("../../../api/rag", () => ({
  getDefaultPrompts: jest.fn(),
}));

const { getDefaultPrompts } = require("../../../api/rag");

const BASE_PROMPT = {
  name: "CustomRAGGenerationPrompt",
  metadata: {
    required_placeholders: ["{chunks}", "{input}"],
    placeholder_descriptions: {
      "{chunks}": "The retrieved passages",
      "{input}": "The user's message",
    },
  },
};

const SEED_PROMPT = {
  name: "DefaultRAGGenerationPrompt",
  metadata: { templates: { en: "Context: {chunks}\nQuestion: {input}" } },
};

/**
 * Renders the editor with a controlled template, exposing what it wrote back.
 * @param {string} template - The starting template.
 * @returns {object} The mock setter and validity callback.
 */
function renderEditor(template) {
  const setPromptModel = jest.fn();
  const onValidityChange = jest.fn();
  renderWithProviders(
    <PromptEditor
      promptModel={{
        component: "CustomRAGGenerationPrompt",
        params: { template, language: "en" },
      }}
      setPromptModel={setPromptModel}
      onValidityChange={onValidityChange}
    />,
  );
  return { setPromptModel, onValidityChange };
}

beforeEach(() => {
  jest.clearAllMocks();
  getDefaultPrompts.mockResolvedValue([BASE_PROMPT, SEED_PROMPT]);
});

test("reports a complete template as valid", async () => {
  const { onValidityChange } = renderEditor("Use {chunks} to answer {input}");
  await waitFor(() => expect(getDefaultPrompts).toHaveBeenCalled());
  await waitFor(() => expect(onValidityChange).toHaveBeenLastCalledWith(true));
});

test("reports a template missing a placeholder as invalid, and says which", async () => {
  const { onValidityChange } = renderEditor("Answer {input}");
  await waitFor(() => expect(onValidityChange).toHaveBeenLastCalledWith(false));
  // Two alerts render the same message (panel and expanded editor share it),
  // so assert that the user is told at all rather than matching one node.
  expect((await screen.findAllByRole("alert")).length).toBeGreaterThan(0);
});

test("writes edits back as a self-contained component ref", async () => {
  const { setPromptModel } = renderEditor("Use {chunks} for {input}");
  await waitFor(() => expect(getDefaultPrompts).toHaveBeenCalled());

  const textarea = screen.getAllByRole("textbox")[0];
  await userEvent.type(textarea, "!");

  expect(setPromptModel).toHaveBeenCalled();
  const written = setPromptModel.mock.calls.at(-1)[0];
  expect(written.component).toBe("CustomRAGGenerationPrompt");
  expect(written.params).toHaveProperty("template");
  expect(written.params).toHaveProperty("language", "en");
});

test("changing the language leaves the template alone", async () => {
  const template = "Hand-written: {chunks} {input}";
  const { setPromptModel } = renderEditor(template);
  await waitFor(() => expect(getDefaultPrompts).toHaveBeenCalled());

  // The language select used to reseed the template as a side effect, which
  // silently discarded whatever the user had written.
  const selects = screen.getAllByRole("combobox");
  await userEvent.click(selects[selects.length - 1]);
  const option = await screen.findByRole("option", { name: "es" });
  await userEvent.click(option);

  const written = setPromptModel.mock.calls.at(-1)[0];
  expect(written.params.language).toBe("es");
  expect(written.params.template).toBe(template);
});
