import React from "react";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import AddIcon from "@mui/icons-material/Add";

import ContentHeader from "../mem-utils/ContentHeader";
import ActionButton from "../mem-utils/ActionButton";
import DataTable from "../mem-utils/DataTable";
import { getUserProjects } from "../mem-utils/mockInstance";
import { useSession } from "../mem-utils/SessionContext";

export default function ProjectsContent({ selectedProject, onSelectProject }) {
  const theme = useTheme();
  const { user } = useSession();
  const projects = getUserProjects(user.id);

  const columns = [
    {
      key: "name",
      label: "Proyecto",
      width: "2fr",
      render: (project, selected) => (
        <Typography
          variant="body2"
          sx={{
            color: theme.palette.text.primary,
            fontWeight: selected ? 500 : 400,
          }}
        >
          {project.name}
        </Typography>
      ),
    },
    {
      key: "id",
      label: "ID",
      render: (project) => (
        <Typography
          variant="body2"
          sx={{
            color: theme.palette.text.disabled,
            fontFamily: '"Geist Mono", monospace',
            fontSize: "0.8rem",
          }}
        >
          {project.id}
        </Typography>
      ),
    },
    { key: "role", label: "Rol" },
  ];

  return (
    <>
      <ContentHeader
        title="Proyectos"
        subtitle={`${projects.length} proyectos asociados a tu cuenta`}
        action={<ActionButton icon={AddIcon}>Nuevo proyecto</ActionButton>}
      />

      <DataTable
        columns={columns}
        rows={projects}
        selectedId={selectedProject?.id}
        onRowClick={onSelectProject}
        actionLabel="Ver detalles"
      />
    </>
  );
}
