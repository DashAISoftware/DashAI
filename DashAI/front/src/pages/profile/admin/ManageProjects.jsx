import React, { useState } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";

import ProfileLayout from "../mem-utils/ProfileLayout";
import DetailPanel, {
  DetailField,
  DetailSection,
} from "../mem-utils/DetailPanel";
import StatusChip from "../mem-utils/StatusChip";
import {
  MOCK_PROJECTS,
  PROJECT_ROLES,
  getUserName,
} from "../mem-utils/mockInstance";
import ManageProjectsContent from "../utils/ManageProjectsContent";

function ProjectDetails({ project, onChange, onClose }) {
  const theme = useTheme();

  const changeMemberRole = (userId, role) =>
    onChange({
      members: project.members.map((member) =>
        member.userId === userId ? { ...member, role } : member,
      ),
    });

  return (
    <DetailPanel
      title={project?.name}
      subtitle={project?.id}
      onClose={onClose}
      emptyMessage="Selecciona un proyecto para gestionar sus miembros."
    >
      {project && (
        <>
          <DetailSection label="Información">
            <DetailField label="Owner">
              {getUserName(project.ownerId)}
            </DetailField>
            <DetailField label="Estado">
              <StatusChip status={project.archived ? "Archivado" : "Activo"} />
            </DetailField>
          </DetailSection>

          <DetailSection label={`Miembros (${project.members.length})`}>
            {project.members.map((member) => (
              <Box
                key={member.userId}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  "& + &": { mt: 1.5 },
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    flex: 1,
                    minWidth: 0,
                    color: theme.palette.text.primary,
                  }}
                >
                  {getUserName(member.userId)}
                </Typography>
                <TextField
                  select
                  size="small"
                  value={member.role}
                  onChange={(event) =>
                    changeMemberRole(member.userId, event.target.value)
                  }
                  // The owner's role changes only by transferring the project
                  disabled={member.userId === project.ownerId}
                  sx={{ width: 120 }}
                >
                  {PROJECT_ROLES.map((role) => (
                    <MenuItem key={role} value={role}>
                      {role}
                    </MenuItem>
                  ))}
                </TextField>
              </Box>
            ))}
          </DetailSection>

          <DetailSection label="Acciones">
            <Button
              variant="outlined"
              size="small"
              color={project.archived ? "primary" : "error"}
              onClick={() => onChange({ archived: !project.archived })}
              sx={{ textTransform: "none" }}
            >
              {project.archived ? "Restaurar proyecto" : "Archivar proyecto"}
            </Button>
            <Typography
              variant="caption"
              sx={{
                display: "block",
                mt: 1,
                color: theme.palette.text.disabled,
              }}
            >
              Un proyecto archivado queda en solo lectura para sus miembros.
            </Typography>
          </DetailSection>
        </>
      )}
    </DetailPanel>
  );
}

export default function ManageProjects() {
  const [projects, setProjects] = useState(MOCK_PROJECTS);
  const [selectedId, setSelectedId] = useState(null);

  const selectedProject =
    projects.find((project) => project.id === selectedId) ?? null;

  const updateSelectedProject = (changes) =>
    setProjects((previous) =>
      previous.map((project) =>
        project.id === selectedId ? { ...project, ...changes } : project,
      ),
    );

  return (
    <ProfileLayout
      title="Gestionar proyectos"
      subtitle="Consulta todos los proyectos de la instancia, sus miembros y su estado."
      rightPanel={
        <ProjectDetails
          project={selectedProject}
          onChange={updateSelectedProject}
          onClose={() => setSelectedId(null)}
        />
      }
    >
      <ManageProjectsContent
        projects={projects}
        selectedProjectId={selectedId}
        onSelectProject={setSelectedId}
      />
    </ProfileLayout>
  );
}
