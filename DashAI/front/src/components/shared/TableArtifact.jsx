import { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Box, TablePagination } from "@mui/material";
import { useTheme, alpha } from "@mui/material/styles";

import "./leanDatasetTable/leanDatasetTable.css";

const TABLE_ROWS_PER_PAGE = 5;

/**
 * Table artifact content: a sticky-header table over a fixed-height,
 * independently scrolling body with client-side pagination pinned below it.
 * Reuses LeanDatasetTable's markup/CSS classes so it reads as the same
 * table style, without pulling in that component's dataset-specific
 * features (filtering, sorting, column visibility).
 */
export default function TableArtifact({
  columns,
  rows,
  highlightedCells,
  height,
}) {
  const theme = useTheme();
  const [page, setPage] = useState(0);

  // Reset to the first page whenever the underlying data changes (e.g.
  // navigating to a sibling artifact in the fullscreen lightbox).
  useEffect(() => setPage(0), [rows]);

  const pageStart = page * TABLE_ROWS_PER_PAGE;
  const pageRows = rows.slice(pageStart, pageStart + TABLE_ROWS_PER_PAGE);

  return (
    <Box
      className="lean-root"
      sx={{
        height,
        "--lean-header-bg": theme.palette.ui.panelDark,
        "--lean-header-fg": theme.palette.text.primary,
        "--lean-body-bg": theme.palette.ui.panelDark,
        "--lean-row-hover": theme.palette.action.hover,
      }}
    >
      <div className="lean-scroll">
        <table className="lean-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column} className="lean-th">
                  <span className="lean-th-name">{column}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => {
              const rowIndex = pageStart + i;
              return (
                <tr key={rowIndex} className="lean-row">
                  {row.map((value, columnIndex) => (
                    <td
                      key={columnIndex}
                      className="lean-cell"
                      style={
                        highlightedCells.has(`${rowIndex}-${columnIndex}`)
                          ? {
                              backgroundColor: alpha(
                                theme.palette.accent.coral,
                                0.25,
                              ),
                              fontWeight: "bold",
                            }
                          : undefined
                      }
                    >
                      {value === null ? "-" : String(value)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <TablePagination
        component="div"
        sx={{
          backgroundColor: "var(--lean-body-bg)",
          border: "1px solid rgba(128, 128, 128, 0.3)",
          borderTop: "none",
          borderBottomLeftRadius: 4,
          borderBottomRightRadius: 4,
        }}
        count={rows.length}
        page={page}
        rowsPerPage={TABLE_ROWS_PER_PAGE}
        rowsPerPageOptions={[]}
        onPageChange={(_e, p) => setPage(p)}
      />
    </Box>
  );
}

TableArtifact.propTypes = {
  columns: PropTypes.arrayOf(PropTypes.string).isRequired,
  rows: PropTypes.array.isRequired,
  highlightedCells: PropTypes.instanceOf(Set).isRequired,
  height: PropTypes.number.isRequired,
};
