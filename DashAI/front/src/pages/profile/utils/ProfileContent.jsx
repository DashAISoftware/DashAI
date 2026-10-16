import React from "react";
import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import { Link as RouterLink } from "react-router-dom";

import EditButton from "../mem-utils/EditButton";
import { getUserProjects, getUserRequests } from "../mem-utils/mockInstance";

// Number of projects and requests previewed in the profile
const PREVIEW_COUNT = 2;

function SeeAllLink({ to, children }) {
  const theme = useTheme();

  return (
    <Typography
      variant="caption"
      component={RouterLink}
      to={to}
      sx={{
        display: "inline-block",
        mt: 3,
        color: theme.palette.text.secondary,
        textDecoration: "none",
        transition: "color 0.15s",

        "&:hover": {
          color: theme.palette.primary.main,
        },
      }}
    >
      {children}
    </Typography>
  );
}

function PreviewList({ items, emptyMessage }) {
  const theme = useTheme();

  if (items.length === 0) {
    return (
      <Typography
        variant="body2"
        sx={{ mt: 3, color: theme.palette.text.disabled }}
      >
        {emptyMessage}
      </Typography>
    );
  }

  return items.map((item, index) => (
    <Box key={item.id} sx={{ mt: index === 0 ? 3 : 2 }}>
      <Typography variant="body2" sx={{ color: theme.palette.text.primary }}>
        {item.title}
      </Typography>
      <Typography
        variant="caption"
        sx={{
          display: "block",
          mt: 0.5,
          color: theme.palette.text.disabled,
        }}
      >
        {item.detail}
      </Typography>
    </Box>
  ));
}

export default function ProfileContent({ user, onEdit }) {
  const theme = useTheme();
  const projects = getUserProjects(user.id).slice(0, PREVIEW_COUNT);
  const requests = getUserRequests(user.id).slice(0, PREVIEW_COUNT);

  return (
    <Box
      sx={{
        width: "100%",
        minHeight: "100%",

        display: "flex",
        flexDirection: "column",

        p: {
          xs: 3,
          sm: 4,
          md: 5,
        },

        backgroundColor: theme.palette.background.default,

        boxSizing: "border-box",
      }}
    >
      {/* ======================================== */}
      {/* ENCABEZADO DEL PERFIL                    */}
      {/* ======================================== */}

      <Box
        sx={{
          display: "flex",
          minHeight: 220,

          pb: 5,

          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        {/* ---------------------------------------- */}
        {/* Información personal                     */}
        {/* ---------------------------------------- */}

        <Box
          sx={{
            flex: 1,
            pr: 5,

            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 2,
              mt: 2,
            }}
          >
            <Typography
              variant="h4"
              sx={{
                color: theme.palette.text.primary,
              }}
            >
              {user.socialName}
            </Typography>

            <EditButton onClick={onEdit} />
          </Box>

          <Typography
            variant="body2"
            sx={{
              color: theme.palette.text.secondary,
              mt: 1,
            }}
          >
            @{user.nickname}
          </Typography>

          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              gap: 2,
              mt: 3,
            }}
          >
            {user.github && (
              <Typography
                variant="body2"
                sx={{
                  color: theme.palette.text.secondary,
                }}
              >
                GitHub · {user.github}
              </Typography>
            )}

            {user.linkedin && (
              <Typography
                variant="body2"
                sx={{
                  color: theme.palette.text.secondary,
                }}
              >
                LinkedIn · {user.linkedin}
              </Typography>
            )}
          </Box>
        </Box>

        {/* ---------------------------------------- */}
        {/* Foto + biografía                         */}
        {/* ---------------------------------------- */}

        <Box
          sx={{
            flex: 1,
            pl: 5,

            display: "flex",
            alignItems: "center",
            gap: 4,
          }}
        >
          {/* Foto de perfil */}

          <Box
            sx={{
              width: 112,
              height: 112,
              flexShrink: 0,

              borderRadius: "50%",
              border: `1px solid ${theme.palette.divider}`,

              display: "flex",
              alignItems: "center",
              justifyContent: "center",

              backgroundColor: theme.palette.background.box,
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: theme.palette.text.disabled,
              }}
            >
              FOTO
            </Typography>
          </Box>

          {/* Biografía */}

          <Box
            sx={{
              flex: 1,
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{
                color: theme.palette.text.primary,
              }}
            >
              SOBRE MÍ
            </Typography>

            <Typography
              variant="body2"
              sx={{
                mt: 2,
                color: user.bio
                  ? theme.palette.text.secondary
                  : theme.palette.text.disabled,
                lineHeight: 1.7,
              }}
            >
              {user.bio || "Aún no has escrito una biografía."}
            </Typography>

            <Link
              component="button"
              type="button"
              variant="caption"
              onClick={onEdit}
              underline="hover"
              sx={{
                display: "block",
                mt: 2,
                color: theme.palette.text.disabled,

                "&:hover": {
                  color: theme.palette.primary.main,
                },
              }}
            >
              Editar biografía
            </Link>
          </Box>
        </Box>
      </Box>

      {/* ======================================== */}
      {/* GRILLA DE INFORMACIÓN                    */}
      {/* ======================================== */}

      <Box
        sx={{
          flex: 1,

          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* ====================================== */}
        {/* FILA SUPERIOR                          */}
        {/* ====================================== */}

        <Box
          sx={{
            flex: 1,

            display: "flex",

            borderBottom: `1px solid ${theme.palette.divider}`,
          }}
        >
          {/* ------------------------------------ */}
          {/* Contacto                             */}
          {/* ------------------------------------ */}

          <Box
            sx={{
              flex: 1,
              p: 4,

              borderRight: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{
                color: theme.palette.text.primary,
              }}
            >
              CONTACTO
            </Typography>

            <Typography
              variant="body2"
              sx={{
                mt: 3,
                color: theme.palette.text.secondary,
              }}
            >
              ✉ {user.email}
            </Typography>

            {user.phone && (
              <Typography
                variant="body2"
                sx={{
                  mt: 2,
                  color: theme.palette.text.secondary,
                }}
              >
                ☎ {user.phone}
              </Typography>
            )}
          </Box>

          {/* ------------------------------------ */}
          {/* Organización                         */}
          {/* ------------------------------------ */}

          <Box
            sx={{
              flex: 1,
              p: 4,
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{
                color: theme.palette.text.primary,
              }}
            >
              ORGANIZACIÓN
            </Typography>

            <Typography
              variant="body2"
              sx={{
                mt: 3,
                color: theme.palette.text.primary,
              }}
            >
              {user.organization || "Sin organización"}
            </Typography>

            <Typography
              variant="body2"
              sx={{
                mt: 2,
                color: theme.palette.text.secondary,
              }}
            >
              {user.position}
            </Typography>

            <Typography
              variant="caption"
              sx={{
                display: "block",
                mt: 2,
                color: theme.palette.text.disabled,
              }}
            >
              Rol DashAI: {user.globalRole}
            </Typography>
          </Box>
        </Box>

        {/* ====================================== */}
        {/* FILA INFERIOR                          */}
        {/* ====================================== */}

        <Box
          sx={{
            flex: 1,

            display: "flex",
          }}
        >
          {/* ------------------------------------ */}
          {/* Proyectos                            */}
          {/* ------------------------------------ */}

          <Box
            sx={{
              flex: 1,
              p: 4,

              borderRight: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{
                color: theme.palette.text.primary,
              }}
            >
              PROYECTOS
            </Typography>

            <PreviewList
              items={projects.map((project) => ({
                id: project.id,
                title: project.name,
                detail: project.role,
              }))}
              emptyMessage="Aún no perteneces a ningún proyecto."
            />

            <SeeAllLink to="/app/profile/projects">
              Ver todos los proyectos →
            </SeeAllLink>
          </Box>

          {/* ------------------------------------ */}
          {/* Solicitudes                          */}
          {/* ------------------------------------ */}

          <Box
            sx={{
              flex: 1,
              p: 4,
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{
                color: theme.palette.text.primary,
              }}
            >
              SOLICITUDES
            </Typography>

            <PreviewList
              items={requests.map((request) => ({
                id: request.id,
                title: request.subject,
                detail: request.status,
              }))}
              emptyMessage="No has realizado solicitudes."
            />

            <SeeAllLink to="/app/profile/requests">
              Ver todas las solicitudes →
            </SeeAllLink>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
