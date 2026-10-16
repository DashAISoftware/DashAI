import React, { useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import InputAdornment from "@mui/material/InputAdornment";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";

import DetailPanel, {
  DetailField,
  DetailSection,
} from "../mem-utils/DetailPanel";
import FormActions from "../mem-utils/FormActions";
import { maskEmail } from "../mem-utils/format";
import { EMAIL_PATTERN, NICKNAME_PATTERN } from "../mem-utils/validation";

function CloseButton({ onClick }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 3 }}>
      <Button
        variant="text"
        size="small"
        onClick={onClick}
        sx={{ textTransform: "none" }}
      >
        Cerrar
      </Button>
    </Box>
  );
}

export function NicknameForm({ nickname, onSave, onClose }) {
  const [draft, setDraft] = useState(nickname);

  const invalid = !NICKNAME_PATTERN.test(draft);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSave(draft);
    onClose();
  };

  return (
    <DetailPanel
      title="Editar nickname"
      subtitle={`Actual: @${nickname}`}
      onClose={onClose}
    >
      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          label="Nickname"
          value={draft}
          onChange={(event) => setDraft(event.target.value.trim())}
          size="small"
          fullWidth
          autoFocus
          error={draft !== "" && invalid}
          helperText="Entre 3 y 20 caracteres: letras, números, punto o guion bajo."
        />
        <FormActions
          onCancel={onClose}
          disabled={invalid || draft === nickname}
          sx={{ mt: 2 }}
        />
      </Box>
    </DetailPanel>
  );
}

export function EmailRequestForm({
  currentEmail,
  pendingEmail,
  onSubmit,
  onClose,
}) {
  const theme = useTheme();
  const [email, setEmail] = useState("");
  const [reason, setReason] = useState("");

  const invalid =
    !EMAIL_PATTERN.test(email) ||
    email.toLowerCase() === currentEmail.toLowerCase();

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit(email);
  };

  return (
    <DetailPanel
      title="Cambio de correo"
      subtitle={`Actual: ${maskEmail(currentEmail)}`}
      onClose={onClose}
    >
      {pendingEmail ? (
        <>
          <Alert severity="info">
            Tu solicitud está pendiente de aprobación por la organización.
          </Alert>

          <DetailSection label="Solicitud">
            <DetailField label="Nuevo correo">{pendingEmail}</DetailField>
            <DetailField label="Estado">Pendiente</DetailField>
          </DetailSection>

          <CloseButton onClick={onClose} />
        </>
      ) : (
        <Box component="form" onSubmit={handleSubmit}>
          <Typography
            variant="body2"
            sx={{ color: theme.palette.text.secondary, lineHeight: 1.6, mb: 3 }}
          >
            Tu correo es administrado por la organización. El cambio quedará
            pendiente hasta que un administrador lo apruebe.
          </Typography>

          <TextField
            label="Nuevo correo"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value.trim())}
            size="small"
            fullWidth
            autoFocus
            error={email !== "" && invalid}
            helperText={
              email !== "" && invalid
                ? "Ingresa un correo válido y distinto del actual."
                : " "
            }
          />

          <TextField
            label="Motivo (opcional)"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            size="small"
            fullWidth
            multiline
            minRows={3}
            sx={{ mt: 1 }}
          />

          <FormActions
            onCancel={onClose}
            submitLabel="Enviar solicitud"
            disabled={invalid}
            sx={{ mt: 2 }}
          />
        </Box>
      )}
    </DetailPanel>
  );
}
