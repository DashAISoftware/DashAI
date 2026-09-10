import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Stack,
  TextField,
  Button,
  Typography,
  Box,
  IconButton,
  InputAdornment,
  Tooltip,
} from "@mui/material";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import VisibilityOffOutlinedIcon from "@mui/icons-material/VisibilityOffOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import CloseIcon from "@mui/icons-material/Close";
import VpnKeyOutlinedIcon from "@mui/icons-material/VpnKeyOutlined";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import {
  getCredentials,
  authenticateCredential,
  deleteCredential,
} from "../../api/credentials";
import { setCredentialStatus, setCredentialStatuses } from "./credentialStatus";

function CredentialRow({ credential, onChanged }) {
  const { t } = useTranslation("credentials");
  const { enqueueSnackbar } = useSnackbar();
  const [key, setKey] = useState(credential.key ?? "");
  const [showKey, setShowKey] = useState(false);
  const [busy, setBusy] = useState(false);

  const authed = credential.is_authenticated;

  const handleVerify = async () => {
    setBusy(true);
    try {
      const { is_authenticated } = await authenticateCredential(
        credential.name,
        key,
      );
      // Broadcast so every open component list re-derives its lock state
      // without a manual refresh.
      setCredentialStatus(credential.name, is_authenticated);
      enqueueSnackbar(t("verifySuccess"), { variant: "success" });
      onChanged();
    } catch {
      enqueueSnackbar(t("verifyError"), { variant: "error" });
    } finally {
      setBusy(false);
    }
  };

  const handleRemove = async () => {
    setBusy(true);
    try {
      const { is_authenticated } = await deleteCredential(credential.name);
      setCredentialStatus(credential.name, is_authenticated);
      setKey("");
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Box
      sx={(theme) => ({
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 2,
        p: 2,
        transition: "border-color 0.15s, background 0.15s",
        "&:hover": { borderColor: theme.palette.text.disabled },
      })}
    >
      {/* Identity + status */}
      <Stack direction="row" alignItems="flex-start" spacing={1.5}>
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {credential.display_name}
          </Typography>
          {credential.description && (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", mt: 0.25, lineHeight: 1.4 }}
            >
              {credential.description}
            </Typography>
          )}
        </Box>
        <Stack
          direction="row"
          alignItems="center"
          spacing={0.75}
          sx={{ flexShrink: 0, mt: 0.25 }}
        >
          <Box
            sx={(theme) => ({
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: authed
                ? theme.palette.success.main
                : theme.palette.text.disabled,
            })}
          />
          <Typography
            variant="caption"
            sx={(theme) => ({
              color: authed
                ? theme.palette.success.main
                : theme.palette.text.secondary,
              fontWeight: 500,
            })}
          >
            {authed ? t("authenticated") : t("notAuthenticated")}
          </Typography>
        </Stack>
      </Stack>

      {/* Key input + actions */}
      <Stack
        direction="row"
        spacing={1.5}
        alignItems="center"
        sx={{ mt: 1.75 }}
      >
        <TextField
          size="small"
          fullWidth
          type={showKey ? "text" : "password"}
          placeholder={t("keyPlaceholder")}
          value={key}
          onChange={(e) => setKey(e.target.value)}
          sx={{ "& input": { fontFamily: "monospace", fontSize: 13 } }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  size="small"
                  aria-label="toggle key visibility"
                  onClick={() => setShowKey((prev) => !prev)}
                  edge="end"
                >
                  {showKey ? (
                    <VisibilityOffOutlinedIcon fontSize="small" />
                  ) : (
                    <VisibilityOutlinedIcon fontSize="small" />
                  )}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        <Button
          onClick={handleVerify}
          disabled={busy || !key}
          variant="contained"
          disableElevation
          sx={{ minWidth: 96, height: 40, flexShrink: 0 }}
        >
          {t("verify")}
        </Button>
        {authed && (
          <Tooltip title={t("remove")}>
            <span>
              <IconButton
                onClick={handleRemove}
                disabled={busy}
                color="error"
                aria-label={t("remove")}
                sx={{ flexShrink: 0 }}
              >
                <DeleteOutlineIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        )}
      </Stack>
    </Box>
  );
}

CredentialRow.propTypes = {
  credential: PropTypes.object.isRequired,
  onChanged: PropTypes.func.isRequired,
};

export default function CredentialsDialog({ open, onClose }) {
  const { t } = useTranslation("credentials");
  const [credentials, setCredentials] = useState([]);

  const refresh = async () => {
    try {
      const data = await getCredentials();
      const list = Array.isArray(data) ? data : [];
      setCredentials(list);
      // Keep the shared store in sync with the freshly fetched truth.
      setCredentialStatuses(list);
    } catch {
      // silently ignore fetch errors (e.g. in test environments)
    }
  };

  useEffect(() => {
    if (open) {
      refresh();
    }
  }, [open]);

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ pb: 1, bgcolor: "background.paper" }}>
        <Stack direction="row" alignItems="flex-start" spacing={1.5}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              {t("title")}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t("subtitle")}
            </Typography>
          </Box>
          <IconButton
            onClick={onClose}
            aria-label="close"
            size="small"
            sx={{ mt: -0.5, mr: -0.5 }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
      </DialogTitle>
      <DialogContent
        dividers
        sx={{ pt: 3, pb: 3, bgcolor: "background.paper" }}
      >
        <Stack spacing={1.5} sx={{ mt: 0.5 }}>
          {credentials.map((credential) => (
            <CredentialRow
              key={credential.name}
              credential={credential}
              onChanged={refresh}
            />
          ))}
        </Stack>
      </DialogContent>
    </Dialog>
  );
}

CredentialsDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};
