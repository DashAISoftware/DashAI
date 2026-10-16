import React from "react";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import { Link as RouterLink } from "react-router-dom";

import AlternateEmailIcon from "@mui/icons-material/AlternateEmail";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import MailOutlineIcon from "@mui/icons-material/MailOutline";

import EditButton from "../mem-utils/EditButton";
import { maskEmail } from "../mem-utils/format";

function ProfileRow({
  title,
  description,
  value,
  action,
  icon: Icon,
  disabled = false,
}) {
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 3,
        py: 3,
      }}
    >
      {/* Icon */}

      {Icon && (
        <Box
          sx={{
            width: 38,
            height: 38,
            flexShrink: 0,

            display: "flex",
            alignItems: "center",
            justifyContent: "center",

            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 1.5,

            color: theme.palette.text.secondary,
          }}
        >
          <Icon sx={{ fontSize: 18 }} />
        </Box>
      )}

      {/* Information */}

      <Box
        sx={{
          flex: 1,
          minWidth: 0,
        }}
      >
        <Typography
          variant="body2"
          sx={{
            color: theme.palette.text.primary,
            fontWeight: 500,
          }}
        >
          {title}
        </Typography>

        {value && (
          <Typography
            variant="body2"
            sx={{
              color: disabled
                ? theme.palette.text.disabled
                : theme.palette.text.secondary,
              mt: 0.5,
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {value}
          </Typography>
        )}

        {description && (
          <Typography
            variant="caption"
            sx={{
              display: "block",
              color: theme.palette.text.disabled,
              mt: 0.5,
              lineHeight: 1.5,
            }}
          >
            {description}
          </Typography>
        )}
      </Box>

      {/* Action */}

      {action && (
        <EditButton
          withIcon={action.type === "edit"}
          onClick={action.onClick}
          disabled={disabled}
        >
          {action.label}
        </EditButton>
      )}
    </Box>
  );
}

function Section({ title, description, children }) {
  const theme = useTheme();

  return (
    <Box>
      <Typography
        variant="h6"
        sx={{
          color: theme.palette.text.primary,
        }}
      >
        {title}
      </Typography>

      {description && (
        <Typography
          variant="body2"
          sx={{
            color: theme.palette.text.disabled,
            mt: 0.5,
            mb: 2,
          }}
        >
          {description}
        </Typography>
      )}

      <Box>{children}</Box>
    </Box>
  );
}

/**
 * Sensitive or organization-managed account data. Each action calls
 * `onEdit` with the key of the form to open ("nickname", "email",
 * "password").
 */
export default function ManageProfileContent({ user, pendingEmail, onEdit }) {
  const theme = useTheme();

  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: 1100,
        mx: "auto",
      }}
    >
      <Typography
        variant="body2"
        sx={{ color: theme.palette.text.disabled, mb: 6 }}
      >
        Tu nombre, biografía, teléfono y redes se editan desde{" "}
        <Link component={RouterLink} to="/app/profile">
          tu perfil
        </Link>
        .
      </Typography>

      {/* ======================================= */}
      {/* IDENTIDAD                               */}
      {/* ======================================= */}

      <Section
        title="Identidad"
        description="Identificadores únicos de tu cuenta dentro de DashAI."
      >
        <ProfileRow
          title="Nickname"
          value={`@${user.nickname}`}
          description="Identificador utilizado para mencionarte y compartir proyectos contigo."
          action={{
            label: "Editar",
            type: "edit",
            onClick: () => onEdit("nickname"),
          }}
          icon={AlternateEmailIcon}
        />

        <Divider />

        <ProfileRow
          title="Correo electrónico"
          value={maskEmail(user.email)}
          description={
            pendingEmail
              ? `Solicitud de cambio pendiente: ${pendingEmail}`
              : "El correo está asociado a tu cuenta y puede estar administrado por tu organización."
          }
          action={{
            label: pendingEmail ? "Ver solicitud" : "Solicitar cambio",
            type: "request",
            onClick: () => onEdit("email"),
          }}
          icon={MailOutlineIcon}
        />
      </Section>

      {/* ======================================= */}
      {/* SEGURIDAD                               */}
      {/* ======================================= */}

      <Box sx={{ mt: 6 }}>
        <Section
          title="Seguridad"
          description="Gestiona los mecanismos de acceso y seguridad de tu cuenta."
        >
          <ProfileRow
            title="Contraseña"
            value="••••••••••••"
            description="Por seguridad, el cambio de contraseña se realiza desde una vista independiente."
            action={{
              label: "Cambiar contraseña",
              type: "security",
              onClick: () => onEdit("password"),
            }}
            icon={LockOutlinedIcon}
          />
        </Section>
      </Box>

      {/* ======================================= */}
      {/* INFORMACIÓN ADMINISTRADA                */}
      {/* ======================================= */}

      <Box sx={{ mt: 6 }}>
        <Section
          title="Información administrada por la organización"
          description="Estos datos no pueden modificarse directamente desde tu perfil."
        >
          <ProfileRow
            title="Nombre legal"
            value={user.legalName}
            description="Este dato es administrado por la organización."
            disabled
          />

          <Divider />

          <ProfileRow
            title="Organización"
            value={user.organization}
            description="Organización a la que pertenece tu cuenta."
            disabled
          />

          <Divider />

          <ProfileRow
            title="Cargo"
            value={user.position}
            description="Cargo o posición registrada por la organización."
            disabled
          />

          <Divider />

          <ProfileRow
            title="Roles y permisos"
            value={user.globalRole}
            description="Los roles asociados a proyectos y organizaciones son administrados según las políticas correspondientes."
            disabled
          />
        </Section>
      </Box>
    </Box>
  );
}
