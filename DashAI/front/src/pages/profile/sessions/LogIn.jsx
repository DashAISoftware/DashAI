import React, { useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { Link as RouterLink, useLocation, useNavigate } from "react-router-dom";

import AuthCard from "../mem-utils/AuthCard";
import PasswordField from "../mem-utils/PasswordField";
import { useSession } from "../mem-utils/SessionContext";
import { resetDemoData } from "../mem-utils/authService";
import { MOCK_USERS } from "../mem-utils/mockInstance";
import { EMAIL_PATTERN } from "../mem-utils/validation";

/* ==========================================================================
 * DEBUG — demo accounts (development only)
 *
 * When SHOW_DEMO_ACCOUNTS is true, the login view shows extra tools to test
 * the app quickly:
 *   - Buttons that fill in the credentials of a regular user and of an
 *     administrator (they only fill the form; you still press "Iniciar
 *     sesión", so the normal login flow runs).
 *   - A button that resets the demo data stored in this browser (new
 *     accounts, profile edits and the current session).
 *
 * Set it to false to work only with the existing accounts or new ones.
 * TODO: remove this block and its JSX section before closing the feature.
 * ========================================================================== */
const SHOW_DEMO_ACCOUNTS = true;

const DEMO_ACCOUNTS = [
  { label: "Usuario", userId: "USR-001" },
  { label: "Admin", userId: "USR-006" },
].map(({ label, userId }) => {
  const account = MOCK_USERS.find((user) => user.id === userId);
  return { label, email: account.email, password: account.password };
});

export default function LogIn() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useSession();

  // Register redirects here with the new account's email; RequireAuth sends
  // the path the user wanted to visit
  const justRegistered = Boolean(location.state?.registered);
  const needsLogin = location.state?.reason === "auth";
  const redirectTo = location.state?.from ?? "/app";

  const [email, setEmail] = useState(location.state?.email ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  const invalid = !EMAIL_PATTERN.test(email) || password === "";

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      await login(email, password);
      navigate(redirectTo, { replace: true });
    } catch (loginError) {
      setError(loginError.message);
    }
  };

  const fillDemoAccount = (account) => {
    setEmail(account.email);
    setPassword(account.password);
    setError(null);
  };

  const handleResetDemoData = async () => {
    await resetDemoData();
    // Reload so the session context reads the default accounts again
    window.location.reload();
  };

  return (
    <AuthCard
      title="Iniciar sesión"
      subtitle="Ingresa con tu cuenta de DashAI"
      footer={
        <>
          ¿No tienes una cuenta?{" "}
          <Link component={RouterLink} to="/app/register">
            Regístrate
          </Link>
        </>
      }
    >
      {needsLogin && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Para acceder a esta funcionalidad debes iniciar sesión.
        </Alert>
      )}

      {justRegistered && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Cuenta creada. Ya puedes iniciar sesión.
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          label="Correo electrónico"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => {
            setEmail(event.target.value.trim());
            setError(null);
          }}
          size="small"
          fullWidth
          autoFocus={!email}
        />

        <PasswordField
          label="Contraseña"
          autoComplete="current-password"
          value={password}
          onChange={(event) => {
            setPassword(event.target.value);
            setError(null);
          }}
          autoFocus={Boolean(email)}
          sx={{ mt: 2 }}
        />

        <Button
          type="submit"
          variant="contained"
          fullWidth
          disableElevation
          disabled={invalid}
          sx={{ mt: 3, textTransform: "none" }}
        >
          Iniciar sesión
        </Button>
      </Box>

      {/* DEBUG — demo accounts, see SHOW_DEMO_ACCOUNTS at the top */}
      {SHOW_DEMO_ACCOUNTS && (
        <Box
          sx={{
            mt: 3,
            p: 2,
            border: "1px dashed",
            borderColor: "warning.main",
            borderRadius: 1,
          }}
        >
          <Typography
            variant="caption"
            sx={{ display: "block", mb: 1, color: "warning.main" }}
          >
            Modo desarrollo: cuentas de prueba
          </Typography>

          <Box sx={{ display: "flex", gap: 1 }}>
            {DEMO_ACCOUNTS.map((account) => (
              <Button
                key={account.label}
                variant="outlined"
                size="small"
                color="warning"
                onClick={() => fillDemoAccount(account)}
                sx={{ flex: 1, textTransform: "none" }}
              >
                {account.label}
              </Button>
            ))}
          </Box>

          <Button
            size="small"
            color="warning"
            onClick={handleResetDemoData}
            sx={{ mt: 1, textTransform: "none" }}
          >
            Restablecer datos de prueba
          </Button>
        </Box>
      )}
    </AuthCard>
  );
}
