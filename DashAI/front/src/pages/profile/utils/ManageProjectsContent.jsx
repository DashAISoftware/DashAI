import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";

import ContentHeader from "../mem-utils/ContentHeader";
import DataTable from "../mem-utils/DataTable";
import StatusChip from "../mem-utils/StatusChip";
import { getUserName } from "../mem-utils/mockInstance";

export default function ManageProjectsContent({
  projects,
  selectedProjectId,
  onSelectProject,
}) {
  const theme = useTheme();
  const activeCount = projects.filter((project) => !project.archived).length;

  const columns = [
    {
      key: "name",
      label: "Proyecto",
      width: "2fr",
      render: (project, selected) => (
        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="body2"
            sx={{
              color: theme.palette.text.primary,
              fontWeight: selected ? 500 : 400,
            }}
          >
            {project.name}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: theme.palette.text.disabled,
              fontFamily: '"Geist Mono", monospace',
            }}
          >
            {project.id}
          </Typography>
        </Box>
      ),
    },
    {
      key: "ownerId",
      label: "Owner",
      render: (project) => (
        <Typography
          variant="body2"
          sx={{ color: theme.palette.text.secondary }}
        >
          {getUserName(project.ownerId)}
        </Typography>
      ),
    },
    {
      key: "members",
      label: "Miembros",
      render: (project) => (
        <Typography
          variant="body2"
          sx={{ color: theme.palette.text.secondary }}
        >
          {project.members.length}
        </Typography>
      ),
    },
    {
      key: "archived",
      label: "Estado",
      render: (project) => (
        <StatusChip status={project.archived ? "Archivado" : "Activo"} />
      ),
    },
  ];

  return (
    <>
      <ContentHeader
        title="Proyectos del servidor"
        subtitle={`${projects.length} proyectos · ${activeCount} activos`}
      />

      <DataTable
        columns={columns}
        rows={projects}
        selectedId={selectedProjectId}
        onRowClick={(project) => onSelectProject(project.id)}
        actionLabel="Ver detalles"
      />
    </>
  );
}
