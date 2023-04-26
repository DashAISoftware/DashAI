import React from "react";
import { GridActionsCellItem } from "@mui/x-data-grid";
import EditIcon from "@mui/icons-material/Edit";

function EditDatasetModal() {
  const handleEdit = () => {};
  return (
    <GridActionsCellItem
      key="edit-button"
      icon={<EditIcon />}
      label="Edit"
      onClick={handleEdit}
      sx={{ color: "#f1ae61" }}
    />
  );
}

export default EditDatasetModal;
