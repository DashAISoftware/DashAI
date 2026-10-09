import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box, Divider, TablePagination } from "@mui/material";
import { useTheme } from "@mui/material/styles";

import "./leanDatasetTable/leanDatasetTable.css";

const ROWS_PER_PAGE = 10;

/**
 * Default picker for the entries of a grouped artifact: a paginated list of
 * group titles styled like the shared dataset table. Selecting a row calls
 * onSelect with the group index.
 *
 * Deliberately free of any data fetching, so rendering a grouped artifact never
 * drags the dataset API in behind it. Callers wanting a richer picker (a local
 * explainer showing each instance's feature values) supply their own through
 * ArtifactList's `renderGroupSelector`.
 */
export default function ArtifactGroupSelector({
  titles,
  selectedIndex,
  onSelect,
}) {
  const theme = useTheme();
  const [page, setPage] = useState(0);

  const pageStart = page * ROWS_PER_PAGE;
  const pageTitles = titles.slice(pageStart, pageStart + ROWS_PER_PAGE);

  return (
    <Box
      className="lean-root"
      sx={{
        "--lean-header-bg": theme.palette.ui.panelDark,
        "--lean-header-fg": theme.palette.text.primary,
        "--lean-body-bg": theme.palette.ui.panelDark,
        "--lean-row-hover": theme.palette.action.hover,
      }}
    >
      <div className="lean-scroll">
        <table className="lean-table">
          <tbody>
            {pageTitles.map((title, i) => {
              const globalIndex = pageStart + i;
              const isSelected = globalIndex === selectedIndex;
              return (
                <tr
                  key={globalIndex}
                  className="lean-row lean-row--clickable"
                  onClick={() => onSelect(globalIndex)}
                  style={{
                    backgroundColor: isSelected
                      ? theme.palette.action.selected
                      : undefined,
                  }}
                >
                  <td className="lean-cell" title={title}>
                    {title}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <Divider />
      <TablePagination
        component="div"
        sx={{
          backgroundColor: "var(--lean-body-bg)",
          border: "1px solid rgba(128, 128, 128, 0.3)",
          borderTop: "none",
          borderBottomLeftRadius: 4,
          borderBottomRightRadius: 4,
        }}
        count={titles.length}
        page={page}
        rowsPerPage={ROWS_PER_PAGE}
        showFirstButton
        showLastButton
        onPageChange={(_event, newPage) => setPage(newPage)}
        rowsPerPageOptions={[ROWS_PER_PAGE]}
        labelRowsPerPage=""
        slotProps={{ select: { sx: { display: "none" } } }}
      />
    </Box>
  );
}

ArtifactGroupSelector.propTypes = {
  titles: PropTypes.arrayOf(PropTypes.string).isRequired,
  selectedIndex: PropTypes.number,
  onSelect: PropTypes.func.isRequired,
};
