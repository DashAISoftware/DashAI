import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Box,
} from "@mui/material";
import WarningIcon from "@mui/icons-material/Warning";
import ErrorIcon from "@mui/icons-material/Error";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import { validateTypeChanges } from "../../../api/datasets";
import { useTranslation } from "react-i18next";

// The backend reads a Date column's strptime format off the data, so the
// confirmed change has to carry what it resolved rather than what we sent.
const withResolvedDtypes = (typeChanges, validationResult) => {
  const resolved = validationResult?.resolved_dtypes || {};
  return Object.fromEntries(
    Object.entries(typeChanges).map(([column, change]) => [
      column,
      resolved[column] ? { ...change, new_dtype: resolved[column] } : change,
    ]),
  );
};

export const TypeChangeValidator = ({
  open,
  onClose,
  onConfirm,
  file,
  typeChanges,
  params,
}) => {
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const { t } = useTranslation(["datasets", "common"]);

  const validateChanges = async () => {
    if (!file) {
      setValidationResult({ valid: true, errors: {}, warnings: {} });
      return;
    }
    setValidating(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("type_changes", JSON.stringify(typeChanges));
      formData.append("params", JSON.stringify(params));

      const result = await validateTypeChanges(formData);
      setValidationResult(result);
    } catch (error) {
      console.error("Validation failed:", error);
      setValidationResult({
        valid: false,
        errors: { general: "Validation request failed: " + error.message },
        warnings: {},
      });
    } finally {
      setValidating(false);
    }
  };

  useEffect(() => {
    if (open) {
      setValidationResult(null);
      validateChanges();
    }
  }, [open]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t("datasets:label.validateTypeChanges")}</DialogTitle>
      <DialogContent>
        {validating && (
          <Box display="flex" justifyContent="center" alignItems="center" p={6}>
            <CircularProgress />
            <Box ml={4}>{t("datasets:label.validatingTypeChanges")}</Box>
          </Box>
        )}

        {!validating && validationResult && (
          <>
            {validationResult.valid ? (
              <Alert severity="success" icon={<CheckCircleIcon />}>
                {t("datasets:label.allTypeChangesValid")}
              </Alert>
            ) : (
              <>
                <Alert severity="error" icon={<ErrorIcon />} sx={{ mb: 4 }}>
                  {t("datasets:label.someTypeChangesCannotBeApplied")}
                </Alert>
                <List dense>
                  {Object.entries(validationResult.errors).map(
                    ([column, error]) => (
                      <ListItem key={column}>
                        <ListItemText
                          primary={column}
                          secondary={error}
                          primaryTypographyProps={{
                            color: "error",
                            fontWeight: "bold",
                          }}
                        />
                      </ListItem>
                    ),
                  )}
                </List>
              </>
            )}

            {validationResult.warnings &&
              Object.keys(validationResult.warnings).length > 0 && (
                <>
                  <Alert
                    severity="warning"
                    icon={<WarningIcon />}
                    sx={{ mt: 4, mb: 2 }}
                  >
                    {t("datasets:label.typeChangeWarnings")}
                  </Alert>
                  <List dense>
                    {Object.entries(validationResult.warnings).map(
                      ([column, warning]) => (
                        <ListItem key={column}>
                          <ListItemText
                            primary={column}
                            secondary={warning}
                            primaryTypographyProps={{ fontWeight: "medium" }}
                          />
                        </ListItem>
                      ),
                    )}
                  </List>
                </>
              )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="inherit">
          {t("common:cancel")}
        </Button>
        <Button
          onClick={() =>
            onConfirm(withResolvedDtypes(typeChanges, validationResult))
          }
          disabled={!validationResult?.valid || validating}
          variant="contained"
          color="primary"
        >
          {t("datasets:button.applyChanges")}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
