import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import Modal from "@mui/material/Modal";
import Paper from "@mui/material/Paper";
import CloseIcon from "@mui/icons-material/Close";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableRow from "@mui/material/TableRow";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";

export default function InfoModal({
  title,
  subtitle,
  rows,
  extraContent,
  open,
  onClose,
}) {
  const { t } = useTranslation(["common"]);

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="info-modal"
      aria-describedby="information-details"
    >
      <Box
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: { xs: "90%", sm: 500 },
          maxHeight: "85vh",
          display: "flex",
          flexDirection: "column",
          bgcolor: "background.paper",
          borderRadius: 2,
          boxShadow: 12,
          p: 0,
          outline: "none",
        }}
      >
        <Box
          sx={{
            p: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
            flexShrink: 0,
          }}
        >
          <Box>
            <Typography variant="h6" component="h2">
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <CloseIcon />
          </IconButton>
        </Box>

        <Box sx={{ p: 6, overflowY: "auto", flex: 1, minHeight: 0 }}>
          {extraContent}

          {rows.length > 0 && (
            <>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                {t("common:metadata")}
              </Typography>
              <TableContainer
                component={Paper}
                sx={{ bgcolor: "rgba(0,0,0,0.2)" }}
              >
                <Table size="small">
                  <TableBody>
                    {rows.map(({ label, value }) => (
                      <TableRow key={label}>
                        <TableCell
                          component="th"
                          scope="row"
                          sx={{ color: "text.secondary" }}
                        >
                          {label}
                        </TableCell>
                        <TableCell align="right">{value}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </Box>
      </Box>
    </Modal>
  );
}

InfoModal.propTypes = {
  title: PropTypes.node.isRequired,
  subtitle: PropTypes.node,
  rows: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.node.isRequired,
      value: PropTypes.node,
    }),
  ).isRequired,
  extraContent: PropTypes.node,
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};
