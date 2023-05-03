// import React, { useState } from "react";
// import PropTypes from "prop-types";
// import { Form } from "react-bootstrap";
// import {
//   StyledButton,
//   Title,
//   StyledTextInput,
//   StyledSelect,
//   StyledFloatingLabel,
// } from "../styles/globalComponents";
// import ModelsTable from "./ModelsTable";
// import { getFullDefaultValues } from "../utils/values";

// function AddModels({
//   compatibleModels,
//   modelsInTable,
//   setModelsInTable,
//   renderFormFactory,
//   removeModelFromTableFactory,
//   setConfigByTableIndex,
// }) {
//   const [addModelValues, setAddModelValues] = useState({ name: "", type: "" });
//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     if (addModelValues.type !== "" && addModelValues.type !== "none") {
//       const index = modelsInTable.length;
//       setModelsInTable([...modelsInTable, addModelValues]);
//       const fetchedJsonSchema = await fetch(
//         `${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + addModelValues.type}`
//       );
//       const parameterSchema = await fetchedJsonSchema.json();
//       const defaultValues = await getFullDefaultValues(parameterSchema);
//       setConfigByTableIndex(index, addModelValues.type, defaultValues);
//       setAddModelValues({ name: "", type: "" });
//     }
//   };
//   const handleChange = (e) => {
//     setAddModelValues((state) => ({
//       ...state,
//       [e.target.name]: e.target.value,
//     }));
//   };
//   if (compatibleModels.length !== 0) {
//     return (
//       <div>
//         <br />
//         <br />
//         <Title>Add Models</Title>
//         <br />
//         <br />
//         <Form
//           className="d-flex"
//           style={{ display: "flex", flexDirection: "column" }}
//         >
//           <div
//             style={{ display: "flex", flexDirection: "row", gridGap: "2rem" }}
//           >
//             <StyledFloatingLabel className="mb-3" label="nickname (optional)">
//               <StyledTextInput
//                 type="text"
//                 name="name"
//                 value={addModelValues.name}
//                 placeholder="model 1"
//                 onChange={handleChange}
//               />
//             </StyledFloatingLabel>
//             <StyledFloatingLabel className="mb-3" label="model type">
//               <StyledSelect
//                 value={addModelValues.type}
//                 name="type"
//                 onChange={handleChange}
//                 aria-label="Select a model type"
//               >
//                 <option value="none" hidden>
//                   Select model
//                 </option>
//                 {compatibleModels.map((model) => (
//                   <option value={model} key={model}>
//                     {model}
//                   </option>
//                 ))}
//               </StyledSelect>
//             </StyledFloatingLabel>
//           </div>
//           <div>
//             <StyledButton
//               style={{ width: "6.9rem" }}
//               onClick={handleSubmit}
//               variant="dark"
//             >
//               Add model
//             </StyledButton>
//           </div>
//         </Form>
//         <br />
//         <ModelsTable
//           rows={modelsInTable}
//           renderFormFactory={renderFormFactory}
//           removeModelFactory={removeModelFromTableFactory}
//         />
//       </div>
//     );
//   }
//   return <div />;
// }

// AddModels.propTypes = {
//   compatibleModels: PropTypes.arrayOf(PropTypes.string),
//   renderFormFactory: PropTypes.func.isRequired,
//   removeModelFromTableFactory: PropTypes.func.isRequired,
//   setConfigByTableIndex: PropTypes.func.isRequired,
//   modelsInTable: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string))
//     .isRequired,
//   setModelsInTable: PropTypes.func.isRequired,
// };

// AddModels.defaultProps = {
//   compatibleModels: [],
// };

// export default AddModels;
