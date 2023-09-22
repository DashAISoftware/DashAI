export const mainSchema = {
  type: "object",
  title: "KNN",
  properties: {
    n_neighbors: {
      title: "N Neighbors",
      type: "integer",
      default: 5,
      maximum: 10,
      minimum: 0,
    },
    weights: {
      type: "string",
      default: "uniform",
      enum: ["uniform", "distance"],
    },
    algorithm: {
      type: "string",
      default: "auto",
      enum: ["auto", "ball_tree", "kd_tree", "brute"],
    },
    recursive_param: {
      type: "object",
      title: "Recursive",
      properties: {
        choice: {
          type: "string",
        },
      },
    },
  },
  //   required: ["n_neighbors", "weights", "algorithm"],
};

// sub-schemas for recursive parameters

export const modelA = {
  name: "ModelA",
  schema: {
    type: "object",
    title: "ModelA",
    error_msg: "there was an error",
    description: "this is a description of model A",
    properties: {
      prop1: {
        title: "Prop1",
        type: "integer",
        default: 24,
      },
      prop2: {
        title: "Prop2",
        type: "integer",
        default: 25,
      },
      prop3: {
        title: "Prop3",
        type: "integer",
        default: 26,
      },
    },
  },
};

export const modelB = {
  name: "ModelB",
  schema: {
    type: "object",
    title: "ModelB",
    properties: {
      prop4: {
        title: "Prop4",
        type: "integer",
        default: 30,
      },
      prop5: {
        title: "Prop5",
        type: "integer",
        default: 31,
      },
      prop6: {
        title: "Prop6",
        type: "integer",
        default: 32,
      },
    },
  },
};

export const modelC = {
  name: "ModelC",
  schema: {
    type: "object",
    title: "ModelC",
    properties: {
      prop7: {
        title: "Prop7",
        type: "integer",
        default: 0,
        minimum: 0,
      },
      prop8: {
        title: "Prop8",
        type: "integer",
        default: 1,
      },
      prop9: {
        title: "Prop9",
        type: "integer",
        default: 2,
      },
      recProp: {
        title: "Recursive Prop",
        type: "object",
        properties: {},
      },
    },
  },
};
