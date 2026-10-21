import React from "react";
import {
  Box,
  Chip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { getColorByColumnType } from "../../../../utils";
import { kindLabel } from "../../../documents/documentKinds";

function Columns({ data }) {
  const theme = useTheme();
  const { t } = useTranslation(["common", "datasets"]);

  // columns can be an array [{columnName, dataType, ...}] or a plain object {name: type}
  const rows = Array.isArray(data)
    ? data.map((col) => ({
        name: col.columnName ?? col.name ?? String(col),
        type: col.dataType ?? col.valueType ?? col.type ?? null,
        kinds: Array.isArray(col.kinds) ? col.kinds : null,
        positions: Array.isArray(col.positions) ? col.positions : null,
      }))
    : data
      ? Object.entries(data).map(([name, colInfo]) => ({
          name,
          type: colInfo && typeof colInfo === "object" ? colInfo.type : colInfo,
        }))
      : [];

  return (
    <Box>
      <Typography variant="sectionLabel" sx={{ color: "text.secondary" }}>
        {t("common:columns")}
      </Typography>
      <Divider sx={{ mt: 2, mb: 2, borderColor: "ui.borderLight" }} />
      <Table size="small">
        <TableBody>
          {rows.map(({ name, type, kinds, positions }) => (
            <TableRow
              key={name}
              sx={{ "&:last-child td": { borderBottom: 0 } }}
            >
              <TableCell
                sx={{
                  borderColor: "ui.borderLight",
                  py: 3,
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    fontFamily: '"IBM Plex Mono", monospace',
                    color: "text.secondary",
                  }}
                >
                  {name}
                </Typography>
                {kinds && (
                  <Typography variant="caption" color="text.secondary">
                    {kinds.map((kind) => kindLabel(t, kind)).join(", ")}
                  </Typography>
                )}
                {positions && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: "block" }}
                  >
                    {t("datasets:documentNotebook.pickedItems", {
                      positions: positions
                        .map((position) => position + 1)
                        .join(", "),
                    })}
                  </Typography>
                )}
              </TableCell>
              <TableCell
                align="right"
                sx={{ borderColor: "ui.borderLight", py: 2 }}
              >
                {type ? (
                  <Chip
                    label={type}
                    size="small"
                    sx={{
                      backgroundColor: getColorByColumnType(type, theme),
                      color: "#fff",
                      fontFamily: '"IBM Plex Mono", monospace',
                      fontSize: "0.7rem",
                      height: 20,
                    }}
                  />
                ) : (
                  <Typography variant="body2" color="text.disabled">
                    —
                  </Typography>
                )}
              </TableCell>
            </TableRow>
          ))}
          {rows.length === 0 && (
            <TableRow>
              <TableCell colSpan={2} sx={{ borderBottom: 0 }}>
                <Typography variant="body2" color="text.disabled">
                  {t("common:noItemsAvailable")}
                </Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Box>
  );
}

export default Columns;
