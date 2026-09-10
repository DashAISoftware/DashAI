import React, { memo, useCallback, useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import { useTheme } from "@mui/material/styles";
import { dataTypesbyColumnType, columnTypesList } from "../../utils/typesLists";

const PAGE_SIZE = 10;

const thStyle = {
  padding: "6px 12px",
  fontWeight: 600,
  fontSize: "0.8rem",
  textAlign: "left",
  whiteSpace: "nowrap",
  borderBottom: "2px solid rgba(128,128,128,0.3)",
  verticalAlign: "middle",
};

const tdStyle = {
  padding: "5px 12px",
  fontSize: "0.875rem",
  whiteSpace: "nowrap",
  borderBottom: "1px solid rgba(128,128,128,0.15)",
  verticalAlign: "middle",
};

const selectStyle = {
  fontSize: "0.8rem",
  padding: "4px 6px",
  border: "1px solid rgba(128,128,128,0.4)",
  borderRadius: 4,
  background: "transparent",
  color: "inherit",
  cursor: "pointer",
  outline: "none",
};

const TypeSelect = memo(function TypeSelect({
  id,
  field,
  value,
  options,
  onChange,
  bg,
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(id, field, e.target.value)}
      style={{ ...selectStyle, background: bg }}
    >
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  );
});

TypeSelect.propTypes = {
  id: PropTypes.number.isRequired,
  field: PropTypes.string.isRequired,
  value: PropTypes.string,
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
  onChange: PropTypes.func.isRequired,
  bg: PropTypes.string,
};

function DatasetPreviewTable({
  previewData,
  isEditable,
  columnsSpec,
  setColumnsSpec,
}) {
  const theme = useTheme();
  const [rows, setRows] = useState([]);
  const [page, setPage] = useState(0);
  const bg = theme.palette.background.paper;

  useEffect(() => {
    if (!previewData?.sample?.length) return;
    const columnNames = Object.keys(previewData.schema);
    setRows(
      columnNames.map((name, idx) => {
        const info = previewData.schema[name];
        return {
          id: idx,
          columnName: name,
          example: previewData.sample[0][name],
          columnType: columnsSpec[name]?.type || info.type,
          dataType: columnsSpec[name]?.dtype || info.dtype,
        };
      }),
    );
    setPage(0);
  }, [previewData, columnsSpec]);

  const handleChange = (id, field, newValue) => {
    setRows((prev) =>
      prev.map((row) => {
        if (row.id !== id) return row;
        if (field === "columnType") {
          const baseDataType = dataTypesbyColumnType[newValue]?.[0] || "";
          return { ...row, columnType: newValue, dataType: baseDataType };
        }
        if (field === "dataType") return { ...row, dataType: newValue };
        return row;
      }),
    );

    const columnName = rows.find((r) => r.id === id)?.columnName;
    const updated = { ...columnsSpec };
    if (field === "columnType") {
      updated[columnName] = {
        ...updated[columnName],
        type: newValue,
        dtype: dataTypesbyColumnType[newValue]?.[0] || "",
      };
    } else if (field === "dataType") {
      updated[columnName] = { ...updated[columnName], dtype: newValue };
    }
    setColumnsSpec(updated);
  };

  const totalPages = Math.ceil(rows.length / PAGE_SIZE);
  const pageRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div>
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            borderCollapse: "collapse",
            width: "100%",
            tableLayout: "auto",
          }}
        >
          <thead>
            <tr style={{ background: theme.palette.ui?.panelDark }}>
              <th style={thStyle}>Column name</th>
              <th style={thStyle}>Example</th>
              <th style={thStyle}>Column type</th>
              <th style={thStyle}>Data type</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row) => {
              const isImage =
                row.columnType === "Image" &&
                typeof row.example === "string" &&
                row.example.startsWith("data:image");
              const dtypeOptions = dataTypesbyColumnType[row.columnType] || [];
              return (
                <tr key={row.id}>
                  <td style={tdStyle}>{row.columnName}</td>
                  <td style={tdStyle}>
                    {isImage ? (
                      <img
                        src={row.example}
                        alt="preview"
                        style={{
                          maxHeight: 48,
                          maxWidth: 48,
                          objectFit: "contain",
                        }}
                      />
                    ) : (
                      String(row.example ?? "")
                    )}
                  </td>
                  <td style={tdStyle}>
                    {isEditable ? (
                      <TypeSelect
                        id={row.id}
                        field="columnType"
                        value={row.columnType}
                        options={columnTypesList}
                        onChange={handleChange}
                        bg={bg}
                      />
                    ) : (
                      row.columnType
                    )}
                  </td>
                  <td style={tdStyle}>
                    {isEditable && dtypeOptions.length > 0 ? (
                      <TypeSelect
                        id={row.id}
                        field="dataType"
                        value={row.dataType}
                        options={dtypeOptions}
                        onChange={handleChange}
                        bg={bg}
                      />
                    ) : (
                      row.dataType
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            gap: 8,
            padding: "6px 12px",
            fontSize: "0.8rem",
            color: theme.palette.text.secondary,
          }}
        >
          <span>
            {page * PAGE_SIZE + 1}-
            {Math.min((page + 1) * PAGE_SIZE, rows.length)} of {rows.length}
          </span>
          <button
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
            style={{
              ...selectStyle,
              padding: "2px 8px",
              opacity: page === 0 ? 0.4 : 1,
            }}
          >
            &lt;
          </button>
          <button
            type="button"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
            style={{
              ...selectStyle,
              padding: "2px 8px",
              opacity: page >= totalPages - 1 ? 0.4 : 1,
            }}
          >
            &gt;
          </button>
        </div>
      )}
    </div>
  );
}

DatasetPreviewTable.propTypes = {
  previewData: PropTypes.object.isRequired,
  isEditable: PropTypes.bool,
  columnsSpec: PropTypes.object.isRequired,
  setColumnsSpec: PropTypes.func.isRequired,
};

export default DatasetPreviewTable;
