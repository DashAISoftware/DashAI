import { MOCK_USER } from "./mockUser";

/**
 * Static instance-wide data used by the administration views until they are
 * connected to the backend. Names and permission uids mirror the RBAC tables
 * (Role, Permission, UserRoleProject).
 */

export const CURRENT_USER_ID = "USR-001";

export const GLOBAL_ROLES = ["Administrador", "Miembro"];
export const PROJECT_ROLES = ["Owner", "Editor", "Viewer"];

export const PERMISSIONS = [
  { uid: "datasets.read", category: "Datos", description: "Ver datasets" },
  {
    uid: "datasets.write",
    category: "Datos",
    description: "Crear y modificar datasets",
  },
  {
    uid: "notebooks.write",
    category: "Datos",
    description: "Crear y modificar notebooks",
  },
  {
    uid: "models.read",
    category: "Modelos",
    description: "Ver sesiones y resultados",
  },
  {
    uid: "models.execute",
    category: "Modelos",
    description: "Entrenar modelos y ejecutar predicciones",
  },
  {
    uid: "workflows.write",
    category: "Modelos",
    description: "Crear y modificar pipelines",
  },
  {
    uid: "generative.read",
    category: "Generativo",
    description: "Ver sesiones generativas",
  },
  {
    uid: "generative.execute",
    category: "Generativo",
    description: "Usar modelos generativos",
  },
  {
    uid: "projects.manage",
    category: "Proyecto",
    description: "Gestionar miembros y roles del proyecto",
  },
  {
    uid: "users.manage",
    category: "Instancia",
    description: "Gestionar usuarios",
  },
  {
    uid: "requests.review",
    category: "Instancia",
    description: "Revisar solicitudes de acceso",
  },
  {
    uid: "roles.manage",
    category: "Instancia",
    description: "Gestionar roles y permisos",
  },
  {
    uid: "instance.manage",
    category: "Instancia",
    description: "Gestionar plugins y actualizaciones",
  },
];

const ALL_PERMISSIONS = PERMISSIONS.map((permission) => permission.uid);

export const MOCK_ROLES = [
  {
    id: "ROLE-ADMIN",
    name: "Administrador",
    scope: "Global",
    system: true,
    description: "Acceso total a la instancia de DashAI.",
    permissions: ALL_PERMISSIONS,
  },
  {
    id: "ROLE-MEMBER",
    name: "Miembro",
    scope: "Global",
    system: false,
    description: "Usuario de la organización sin privilegios de gestión.",
    permissions: ["datasets.read", "models.read"],
  },
  {
    id: "ROLE-OWNER",
    name: "Owner",
    scope: "Proyecto",
    system: false,
    description: "Responsable del proyecto y de sus integrantes.",
    permissions: [
      "datasets.read",
      "datasets.write",
      "notebooks.write",
      "models.read",
      "models.execute",
      "workflows.write",
      "generative.read",
      "generative.execute",
      "projects.manage",
    ],
  },
  {
    id: "ROLE-EDITOR",
    name: "Editor",
    scope: "Proyecto",
    system: false,
    description: "Puede trabajar con los datos y modelos del proyecto.",
    permissions: [
      "datasets.read",
      "datasets.write",
      "notebooks.write",
      "models.read",
      "models.execute",
      "workflows.write",
    ],
  },
  {
    id: "ROLE-VIEWER",
    name: "Viewer",
    scope: "Proyecto",
    system: false,
    description: "Solo puede consultar el contenido del proyecto.",
    permissions: ["datasets.read", "models.read"],
  },
];

export const MOCK_USERS = [
  {
    id: CURRENT_USER_ID,
    name: MOCK_USER.socialName,
    nickname: MOCK_USER.nickname,
    email: MOCK_USER.email,
    globalRole: MOCK_USER.globalRole,
    active: true,
  },
  {
    id: "USR-002",
    name: "Ana Pérez",
    nickname: "anaperez",
    email: "ana.perez@example.com",
    globalRole: "Miembro",
    active: true,
  },
  {
    id: "USR-003",
    name: "Pedro Muñoz",
    nickname: "pmunoz",
    email: "pedro.munoz@example.com",
    globalRole: "Miembro",
    active: true,
  },
  {
    id: "USR-004",
    name: "Diego Rojas",
    nickname: "drojas",
    email: "diego.rojas@example.com",
    globalRole: "Miembro",
    active: true,
  },
  {
    id: "USR-005",
    name: "Catalina Fuentes",
    nickname: "cfuentes",
    email: "catalina.fuentes@example.com",
    globalRole: "Miembro",
    active: false,
  },
];

export const MOCK_PROJECTS = [
  {
    id: "PRJ-001",
    name: "Proyecto de Machine Learning",
    ownerId: CURRENT_USER_ID,
    archived: false,
    members: [
      { userId: CURRENT_USER_ID, role: "Owner" },
      { userId: "USR-002", role: "Editor" },
      { userId: "USR-003", role: "Editor" },
    ],
  },
  {
    id: "PRJ-002",
    name: "Análisis de datasets",
    ownerId: "USR-002",
    archived: false,
    members: [
      { userId: "USR-002", role: "Owner" },
      { userId: CURRENT_USER_ID, role: "Viewer" },
      { userId: "USR-003", role: "Editor" },
    ],
  },
  {
    id: "PRJ-003",
    name: "Modelos generativos",
    ownerId: CURRENT_USER_ID,
    archived: false,
    members: [
      { userId: CURRENT_USER_ID, role: "Owner" },
      { userId: "USR-004", role: "Editor" },
      { userId: "USR-005", role: "Viewer" },
    ],
  },
  {
    id: "PRJ-004",
    name: "Clasificación de imágenes",
    ownerId: "USR-003",
    archived: false,
    members: [
      { userId: "USR-003", role: "Owner" },
      { userId: "USR-004", role: "Editor" },
    ],
  },
  {
    id: "PRJ-005",
    name: "Piloto de encuestas",
    ownerId: "USR-005",
    archived: true,
    members: [{ userId: "USR-005", role: "Owner" }],
  },
];

export const MOCK_REQUESTS = [
  {
    id: "REQ-001",
    subject: "Acceso de edición al proyecto",
    projectId: "PRJ-001",
    requesterId: CURRENT_USER_ID,
    status: "Pendiente",
    permissions: ["datasets.write", "models.execute", "workflows.write"],
    reason:
      "Necesito modificar los datasets utilizados por el workflow de entrenamiento.",
  },
  {
    id: "REQ-002",
    subject: "Acceso a modelos generativos",
    projectId: "PRJ-003",
    requesterId: CURRENT_USER_ID,
    status: "Aprobada",
    permissions: ["generative.read", "generative.execute"],
    reason:
      "Necesito utilizar las herramientas generativas disponibles en el proyecto.",
  },
  {
    id: "REQ-003",
    subject: "Permiso para modificar datasets",
    projectId: "PRJ-002",
    requesterId: CURRENT_USER_ID,
    status: "Rechazada",
    permissions: ["datasets.write"],
    reason:
      "Se requiere acceso de edición para preparar los datos del proyecto.",
  },
  {
    id: "REQ-004",
    subject: "Unirse al proyecto como lector",
    projectId: "PRJ-001",
    requesterId: "USR-004",
    status: "Pendiente",
    permissions: ["datasets.read", "models.read"],
    reason: "Quiero revisar los resultados del entrenamiento para mi informe.",
  },
  {
    id: "REQ-005",
    subject: "Ejecutar entrenamientos",
    projectId: "PRJ-004",
    requesterId: "USR-002",
    status: "Pendiente",
    permissions: ["models.execute"],
    reason: "Debo entrenar una nueva versión del clasificador de imágenes.",
  },
];

export function getUserName(userId) {
  return MOCK_USERS.find((user) => user.id === userId)?.name ?? userId;
}

export function getProjectName(projectId) {
  return (
    MOCK_PROJECTS.find((project) => project.id === projectId)?.name ?? projectId
  );
}
