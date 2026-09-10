import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableRow from "@mui/material/TableRow";
import { formatDate } from "../../utils";
import { useTranslation } from "react-i18next";
import { useTheme } from "@mui/material/styles";
import InfoModal from "../shared/InfoModal";

export default function InfoSessionModal({ sessionData, open, onClose }) {
  const { t } = useTranslation(["generative", "common"]);
  const theme = useTheme();

  // If no session data is provided, don't render anything
  if (!sessionData) return null;

  const rows = [
    { label: t("common:id"), value: sessionData.id },
    { label: t("common:created"), value: formatDate(sessionData.created) },
    {
      label: t("common:lastModified"),
      value: formatDate(sessionData.last_modified),
    },
  ];

  const extraContent = (
    <>
      <Box sx={{ mb: 6 }}>
        <Chip
          label={sessionData.task_name}
          color="primary"
          size="small"
          sx={{ mb: 2 }}
        />
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t("common:model")}:{" "}
          <span style={{ color: theme.palette.text.primary }}>
            {sessionData.model_name}
          </span>
        </Typography>
      </Box>

      <Typography variant="subtitle2" sx={{ mb: 2 }}>
        {t("common:parameters")}:{" "}
      </Typography>
      <TableContainer
        component={Paper}
        sx={{ mb: 6, bgcolor: "rgba(0,0,0,0.2)" }}
      >
        <Table size="small">
          <TableBody>
            {Object.entries(sessionData.parameters || {}).map(
              ([key, value]) => (
                <TableRow key={key}>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ color: "text.secondary" }}
                  >
                    {key.replace(/_/g, " ")}
                  </TableCell>
                  <TableCell align="right">{value}</TableCell>
                </TableRow>
              ),
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );

  return (
    <InfoModal
      title={t("generative:label.sessionInformation")}
      subtitle={sessionData.name}
      rows={rows}
      extraContent={extraContent}
      open={open}
      onClose={onClose}
    />
  );
}
