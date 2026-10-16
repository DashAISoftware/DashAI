import React, { useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import InputAdornment from "@mui/material/InputAdornment";
import Link from "@mui/material/Link";
import TextField from "@mui/material/TextField";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import AuthCard from "../mem-utils/AuthCard";
import PasswordField from "../mem-utils/PasswordField";
import { useSession } from "../mem-utils/SessionContext";
import {
  EMAIL_PATTERN,
  MIN_PASSWORD_LENGTH,
  NICKNAME_PATTERN,
} from "../mem-utils/validation";

export default function Register() {
  const navigate = useNavigate();
  const { register } = useSession();
  const [error, setError] = useState(null);

  const [name, setName] = useState("");
  const [nickname, setNickname] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  // Errors are only shown once the user has typed something
  const nicknameError = nickname !== "" && !NICKNAME_PATTERN.test(nickname);
  const emailError = email !== "" && !EMAIL_PATTERN.test(email);
  const passwordError =
    password !== "" && password.length < MIN_PASSWORD_LENGTH;
  const confirmError = confirm !== "" && confirm !== password;

  const invalid =
    name.trim() === "" ||
    !NICKNAME_PATTERN.test(nickname) ||
    !EMAIL_PATTERN.test(email) ||
    password.length < MIN_PASSWORD_LENGTH ||
    confirm !== password;

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      await register({ name: name.trim(), nickname, email, password });
      navigate("/app/login", { state: { registered: true, email } });
    } catch (registerError) {
      setError(registerError.message);
    }
  };

  return (
    <AuthCard
      title="Registrar cuenta nueva"
      subtitle="Crea tu cuenta para colaborar en proyectos de DashAI"
      footer={
        <>
          ¿Ya tienes una cuenta?{" "}
          <Link component={RouterLink} to="/app/login">
            Inicia sesión
          </Link>
        </>
      }
    >
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          label="Nombre"
          autoComplete="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          size="small"
          fullWidth
          autoFocus
          helperText="Nombre visible para otros miembros."
        />

        <TextField
          label="Nickname"
          autoComplete="username"
          value={nickname}
          onChange={(event) => setNickname(event.target.value.trim())}
          size="small"
          fullWidth
          error={nicknameError}
          helperText="Entre 3 y 20 caracteres: letras, números, punto o guion bajo."
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">@</InputAdornment>
              ),
            },
          }}
          sx={{ mt: 2 }}
        />

        <TextField
          label="Correo electrónico"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value.trim())}
          size="small"
          fullWidth
          error={emailError}
          helperText={emailError ? "Ingresa un correo válido." : " "}
          sx={{ mt: 2 }}
        />

        <PasswordField
          label="Contraseña"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={passwordError}
          helperText={`Mínimo ${MIN_PASSWORD_LENGTH} caracteres.`}
          sx={{ mt: 1 }}
        />

        <PasswordField
          label="Confirmar contraseña"
          autoComplete="new-password"
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
          error={confirmError}
          helperText={confirmError ? "Las contraseñas no coinciden." : " "}
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
          Crear cuenta
        </Button>
      </Box>
    </AuthCard>
  );
}
