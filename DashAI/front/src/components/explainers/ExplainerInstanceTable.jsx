import React from "react";
import PropTypes from "prop-types";

import { getDatasetFile } from "../../api/datasets";
import ArtifactGroupSelector from "../shared/ArtifactGroupSelector";
import LeanDatasetTable from "../shared/leanDatasetTable/LeanDatasetTable";

/**
 * Instance picker for a local explainer's explained rows. When the explainer
 * stored its input rows as a dataset (datasetPath), it renders the shared
 * dataset table (feature values, image thumbnails, pagination). Otherwise, for
 * explainers computed before input rows were persisted, it falls back to the
 * shared title list. Selecting a row calls onSelect with the instance index.
 */
export default function ExplainerInstanceTable({
  datasetPath = null,
  titles,
  selectedIndex,
  onSelect,
}) {
  if (!datasetPath) {
    return (
      <ArtifactGroupSelector
        titles={titles}
        selectedIndex={selectedIndex}
        onSelect={onSelect}
      />
    );
  }

  return (
    <LeanDatasetTable
      fetchPage={(fetchPageIndex, pageSize) =>
        getDatasetFile(datasetPath, fetchPageIndex, pageSize)
      }
      datasetPath={datasetPath}
      initialPageSize={10}
      enableFilters={false}
      enableSearch={false}
      enableColumnVisibility={false}
      enableRowsPerPage={false}
      showExportButton={false}
      selectedRowIndex={selectedIndex}
      onRowClick={(row, globalIndex) => onSelect(globalIndex)}
    />
  );
}

ExplainerInstanceTable.propTypes = {
  datasetPath: PropTypes.string,
  titles: PropTypes.arrayOf(PropTypes.string).isRequired,
  selectedIndex: PropTypes.number,
  onSelect: PropTypes.func.isRequired,
};
