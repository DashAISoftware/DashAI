import React, { useState } from "react";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import { Link as RouterLink } from "react-router-dom";

import ProfileLayout from "../mem-utils/ProfileLayout";
import DetailPanel, { DetailSection } from "../mem-utils/DetailPanel";
import EditableField from "../mem-utils/EditableField";
import { useSession } from "../mem-utils/SessionContext";
import ProfileContent from "../utils/ProfileContent";

const EDITABLE_SECTIONS = [
  {
    label: "Información personal",
    fields: [
      {
        key: "socialName",
        label: "Nombre social",
        description: "Nombre utilizado para identificarte dentro de DashAI.",
        required: true,
      },
      {
        key: "bio",
        label: "Biografía",
        description: "Una breve descripción que otros miembros pueden ver.",
        multiline: true,
      },
    ],
  },
  {
    label: "Contacto",
    fields: [{ key: "phone", label: "Teléfono" }],
  },
  {
    label: "Redes",
    fields: [
      { key: "github", label: "GitHub" },
      { key: "linkedin", label: "LinkedIn" },
    ],
  },
];

function EditProfilePanel({ user, onChange, onClose }) {
  const theme = useTheme();

  return (
    <DetailPanel
      title="Editar perfil"
      subtitle="Los cambios se reflejan en tu perfil"
      onClose={onClose}
    >
      {EDITABLE_SECTIONS.map((section) => (
        <DetailSection key={section.label} label={section.label}>
          {section.fields.map((field) => (
            <EditableField
              key={field.key}
              label={field.label}
              value={user[field.key]}
              description={field.description}
              multiline={field.multiline}
              required={field.required}
              onSave={(value) => onChange(field.key, value)}
            />
          ))}

          {section.label === "Contacto" && (
            <Typography
              variant="caption"
              sx={{
                display: "block",
                mt: 3,
                color: theme.palette.text.disabled,
                lineHeight: 1.5,
              }}
            >
              El correo y el nickname se gestionan desde{" "}
              <Link component={RouterLink} to="/app/profile/account">
                Gestionar cuenta
              </Link>
              .
            </Typography>
          )}
        </DetailSection>
      ))}
    </DetailPanel>
  );
}

export default function Profile() {
  const { user, updateUser } = useSession();
  const [editing, setEditing] = useState(false);

  // Saved in the toy session, so the app bar and other views see the change
  const handleChange = (field, value) =>
    updateUser(user.id, { [field]: value });

  return (
    <ProfileLayout
      contentSx={{ p: { xs: 2, sm: 3, md: 4 } }}
      rightPanel={
        editing ? (
          <EditProfilePanel
            user={user}
            onChange={handleChange}
            onClose={() => setEditing(false)}
          />
        ) : (
          <DetailPanel emptyMessage="Selecciona un proyecto o una solicitud para mostrar información adicional aquí." />
        )
      }
    >
      <ProfileContent user={user} onEdit={() => setEditing(true)} />
    </ProfileLayout>
  );
}
