import { useEffect, useState } from "react";
import { getComponents } from "../api/component";
import { generateYupSchema } from "../utils/schema";

export default function useModelSchema() {
  const [model, setModel] = useState(null);
  const [loading, setLoading] = useState(false);

  const formattedModel = async (schema) => {
    const subforms = {};
    await Promise.all(
      Object.keys(schema.properties)
        .filter((key) => schema.properties[key].type === "object")
        .map(async (key) => {
          const subform = await getComponents({
            model: schema.properties[key].placeholder.component,
          });
          subforms[key] = {
            properties: await formattedModel(subform.schema),
            type: "object",
          };
        }),
    );
    return { ...schema.properties, ...subforms };
  };

  useEffect(() => {
    const getModel = async () => {
      try {
        setLoading(true);
        const result = schemaDefault;
        const formattedSchema = await formattedModel(result?.schema);

        setModel(formattedSchema);
      } catch (error) {
        console.log(error);
      } finally {
        setLoading(false);
      }
    };

    getModel();
  }, []);

  const { schema, initialValues } = model
    ? generateYupSchema(model)
    : { schema: {}, initialValues: {} };

  return {
    modelSchema: model,
    defaultValues: initialValues,
    yupSchema: schema,
    loading,
  };
}

const schemaDefault = {
  name: "NumericalWrapperForText",
  type: "Model",
  configurable_object: true,
  schema: {
    description:
      "NumericalWrapperForText is a metamodel that allows text classification using\ntabular classifiers and a tokenizer.",
    properties: {
      tabular_classifier: {
        description:
          "Tabular model used as the underlying modelto generate the text classifier.",
        parent: "TabularClassificationModel",
        placeholder: { component: "SVC", params: {} },
        properties: {
          component: {
            title: "Component",
            type: "string",
          },
          params: {
            title: "Params",
            type: "object",
          },
        },
        required: ["component", "params"],
        title: "Tabular Classifier",
        type: "object",
      },
      tabular_classifier_duplex: {
        description:
          "Tabular model used as the underlying modelto generate the text classifier.",
        parent: "TabularClassificationModel",
        placeholder: { component: "LogisticRegression", params: {} },
        properties: {
          component: {
            title: "Component",
            type: "string",
          },
          params: {
            title: "Params",
            type: "object",
          },
        },
        required: ["component", "params"],
        title: "Tabular Classifier",
        type: "object",
      },
      ngram_min_n: {
        description: "Minimum n_gram to use in the vectorizer.",
        minimum: 1,
        placeholder: 1,
        title: "Ngram Min N",
        type: "integer",
      },
      ngram_max_n: {
        description: "Maximum n_gram to use in the vectorizer.",
        maximum: 1,
        placeholder: 1,
        title: "Ngram Max N",
        type: "integer",
      },
    },
    required: ["tabular_classifier", "ngram_min_n", "ngram_max_n"],
    title: "NumericalWrapperForTextSchema",
    type: "object",
  },
  description: null,
};
