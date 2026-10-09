import { buildYupSchema, preprocessSchema } from "./utils";

// What pydantic emits for `negative_prompt: Optional[str] = None` next to a
// plain required integer.
const PROPERTIES = {
  negative_prompt: {
    anyOf: [{ type: "string", placeholder: "" }, { type: "null" }],
    default: null,
    title: "Negative Prompt",
  },
  steps: { type: "integer", minimum: 1, title: "Steps" },
} as any;

const schema = buildYupSchema(preprocessSchema(PROPERTIES));

test.each([
  ["empty", ""],
  ["null", null],
  ["missing", undefined],
])("a nullable field accepts a %s value", async (_, value) => {
  await expect(
    schema.validate({ negative_prompt: value, steps: 20 }),
  ).resolves.toBeDefined();
});

test("a field without a default is still required", async () => {
  await expect(schema.validate({ negative_prompt: "" })).rejects.toThrow(
    "Required",
  );
});
