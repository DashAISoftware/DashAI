import PropTypes from "prop-types";
import LeanDatasetTable from "../../shared/leanDatasetTable/LeanDatasetTable";

/**
 * Dataset preview table. Delegates to ``LeanDatasetTable`` which renders a
 * native ``<table>`` with sticky header, server-side pagination, sorting,
 * filtering, column visibility, search highlighting, column rename, and
 * encoder selector for Categorical columns.
 *
 * Props mirror the previous ``MaterialReactTable``-based implementation so
 * existing callers need no changes.
 */
export default function DatasetTable({
  fetchPage,
  initialPageSize = 5,
  deps = [],
  datasetPath,
  datasetId,
  datasetName = "dataset",
  columnTypes = {},
  onEditColumn = null,
  showExportButton = true,
  enableTopToolbar = true,
  enableRowsPerPageSelector = true,
  rowActions = null,
  targetColumn = null,
  editableRows = [],
  infiniteScroll = false,
  loadMoreStep = 25,
  extraActions = null,
  enableRowSelection = false,
  selectedRowIndices = null,
  onRowSelectionChange = null,
}) {
  return (
    <LeanDatasetTable
      fetchPage={fetchPage}
      initialPageSize={initialPageSize}
      deps={deps}
      columnTypes={columnTypes}
      datasetId={datasetId}
      datasetPath={datasetPath}
      datasetName={datasetName}
      onColumnChanged={onEditColumn}
      enableColumnVisibility={enableTopToolbar}
      enableFilters={enableTopToolbar}
      enableSearch={enableTopToolbar}
      enableRowsPerPage={enableRowsPerPageSelector}
      showExportButton={showExportButton && enableTopToolbar}
      rowActions={rowActions}
      targetColumn={targetColumn}
      editableRows={editableRows}
      infiniteScroll={infiniteScroll}
      loadMoreStep={loadMoreStep}
      extraActions={extraActions}
      enableRowSelection={enableRowSelection}
      selectedRowIndices={selectedRowIndices}
      onRowSelectionChange={onRowSelectionChange}
    />
  );
}

DatasetTable.propTypes = {
  fetchPage: PropTypes.func.isRequired,
  initialPageSize: PropTypes.number,
  deps: PropTypes.array,
  datasetPath: PropTypes.string,
  datasetId: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  datasetName: PropTypes.string,
  columnTypes: PropTypes.object,
  onEditColumn: PropTypes.func,
  showExportButton: PropTypes.bool,
  enableTopToolbar: PropTypes.bool,
  enableRowsPerPageSelector: PropTypes.bool,
  rowActions: PropTypes.func,
  targetColumn: PropTypes.string,
  editableRows: PropTypes.array,
  infiniteScroll: PropTypes.bool,
  loadMoreStep: PropTypes.number,
  extraActions: PropTypes.node,
  enableRowSelection: PropTypes.bool,
  selectedRowIndices: PropTypes.instanceOf(Set),
  onRowSelectionChange: PropTypes.func,
};
