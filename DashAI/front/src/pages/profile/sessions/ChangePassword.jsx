import React, { useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import { Link as RouterLink } from "react-router-dom";

import AuthCard from "../mem-utils/AuthCard";
import PasswordField from "../mem-utils/PasswordField";
import { useSession } from "../mem-utils/SessionContext";
import { MIN_PASSWORD_LENGTH } from "../mem-utils/validation";

const ACCOUNT_PATH = "/app/profile/account";

export default function ChangePassword() {
  const { user, changePassword } = useSession();
  const [error, setError] = useState(null);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [done, setDone] = useState(false);

  const tooShort = next !== "" && next.length < MIN_PASSWORD_LENGTH;
  const sameAsCurrent = next !== "" && next === current;
  const mismatch = confirm !== "" && confirm !== next;

  const invalid =
    current === "" ||
    next.length < MIN_PASSWORD_LENGTH ||
    next === current ||
    confirm !== next;

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      await changePassword(current, next);
      setDone(true);
    } catch (submitError) {
      setError(submitError.message);
    }
  };

  let nextHelper = `Mínimo ${MIN_PASSWORD_LENGTH} caracteres.`;
  if (tooShort)
    nextHelper = `Debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
  if (sameAsCurrent) nextHelper = "Debe ser distinta de la contraseña actual.";

  return (
    <AuthCard
      title="Cambiar contraseña"
      subtitle={`${user.socialName} · @${user.nickname}`}
      footer={
        !done && (
          <Link component={RouterLink} to={ACCOUNT_PATH}>
            Volver a gestionar cuenta
          </Link>
        )
      }
    >
      {done ? (
        <>
          <Alert severity="success">
            Contraseña actualizada. Úsala la próxima vez que inicies sesión.
          </Alert>
          <Button
            component={RouterLink}
            to={ACCOUNT_PATH}
            variant="contained"
            fullWidth
            disableElevation
            sx={{ mt: 3, textTransform: "none" }}
          >
            Volver a tu cuenta
          </Button>
        </>
      ) : (
        <Box component="form" onSubmit={handleSubmit}>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <PasswordField
            label="Contraseña actual"
            autoComplete="current-password"
            value={current}
            onChange={(event) => {
              setCurrent(event.target.value);
              setError(null);
            }}
            autoFocus
            helperText=" "
          />

          <PasswordField
            label="Nueva contraseña"
            autoComplete="new-password"
            value={next}
            onChange={(event) => setNext(event.target.value)}
            error={tooShort || sameAsCurrent}
            helperText={nextHelper}
            sx={{ mt: 1 }}
          />

          <PasswordField
            label="Confirmar nueva contraseña"
            autoComplete="new-password"
            value={confirm}
            onChange={(event) => setConfirm(event.target.value)}
            error={mismatch}
            helperText={mismatch ? "Las contraseñas no coinciden." : " "}
            sx={{ mt: 2 }}
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            disableElevation
            disabled={invalid}
            sx={{ mt: 2, textTransform: "none" }}
          >
            Cambiar contraseña
          </Button>
        </Box>
      )}
    </AuthCard>
  );
}
