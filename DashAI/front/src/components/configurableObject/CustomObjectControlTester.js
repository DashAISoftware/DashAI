import { isObjectControl, rankWith } from "@jsonforms/core";

// function that assigns priority on which component is chosen to render the type "object"
export default rankWith(3, isObjectControl);
