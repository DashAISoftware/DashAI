import React, { useMemo } from "react";
import * as Yup from "yup";

export default function useModelSchema() {
  const [modelSchema, setModelSchema] = React.useState({
    name: "LogisticRegression",
    type: "Model",
    configurable_object: true,
    schema: {
      description:
        "Logistic Regression is a supervised classification method that uses a linear\nmodel plus a a logistic funcion to predict binary outcomes (it can be configured\nas multiclass via the one-vs-rest strategy).",
      properties: {
        penalty: {
          anyOf: [
            {
              description: "Specify the norm of the penalty",
              enum: ["l2", "l1", "elasticnet"],
              placeholder: "l2",
              type: "string",
            },
            {
              type: "null",
            },
          ],
          title: "Penalty",
        },
        tol: {
          description: "Tolerance for stopping criteria.",
          minimum: 0,
          placeholder: 0.0001,
          title: "Tol",
          type: "number",
        },
        C: {
          description:
            "Inverse of regularization strength, smaller values specify stronger regularization. Must be a positive number.",
          minimum: 0,
          placeholder: 1,
          title: "C",
          type: "number",
        },
        max_iter: {
          description:
            "Maximum number of iterations taken for the solvers to converge.",
          minimum: 50,
          placeholder: 100,
          title: "Max Iter",
          type: "integer",
        },
      },
      required: ["penalty", "tol", "C", "max_iter"],
      title: "LogisticRegressionSchema",
      type: "object",
    },
    description: null,
  });

  const defaultValues = useMemo(() => {
    return Object.keys(modelSchema.schema.properties).reduce(
      (defaultValues, key) => {
        const propertie = modelSchema.schema.properties[key];

        defaultValues[key] = propertie.anyOf
          ? propertie.anyOf[0].placeholder
          : propertie.placeholder;
        return defaultValues;
      },
      {},
    );
  }, []);

  // Dynamic schema construction
  const schema = Yup.object().shape(
    Object.keys(modelSchema.schema.properties).reduce((acc, key) => {
      const property = modelSchema.schema.properties[key];
      let fieldSchema;

      if (property.anyOf) {
        fieldSchema = Yup.mixed()
          .nullable()
          .when(key, {
            is: (value) => value !== null,
            then: Yup.mixed().oneOf(
              property.anyOf.reduce((types, item) => {
                if (item.type === "string") {
                  if (item.enum) {
                    return types.concat(Yup.string().oneOf(item.enum));
                  } else {
                    return types.concat(Yup.string());
                  }
                } else if (item.type === "number") {
                  types.push(Yup.number().min(item.minimum));
                }
                // Add more types as needed
                return types;
              }, []),
            ),
            otherwise: Yup.mixed().nullable(),
          });
      } else if (property.type === "string") {
        fieldSchema = Yup.string();
      } else if (property.type === "number") {
        fieldSchema = Yup.number().min(property.minimum);
      } else if (property.type === "integer") {
        fieldSchema = Yup.number().integer().min(property.minimum);
      }

      if (property.type !== "null") {
        fieldSchema = fieldSchema.required(`${property.title} is required`);
      }

      return { ...acc, [key]: fieldSchema };
    }, {}),
  );

  console.log(schema);

  return { modelSchema: schema, defaultValues, setModelSchema };
}

// {
//     "C": 1,
//     "coef0": 0,
//     "degree": 3,
//     "gamma": "scale",
//     "kernel": "rbf",
//     "max_iter": -1,
//     "probability": true,
//     "shrinking": true,
//     "tol": 0.001,
//     "verbose": false
// }
