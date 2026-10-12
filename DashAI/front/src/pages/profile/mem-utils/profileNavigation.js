import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import ManageAccountsOutlinedIcon from "@mui/icons-material/ManageAccountsOutlined";
import FolderOutlinedIcon from "@mui/icons-material/FolderOutlined";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import PeopleOutlineIcon from "@mui/icons-material/PeopleOutline";
import FolderSharedOutlinedIcon from "@mui/icons-material/FolderSharedOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import AdminPanelSettingsOutlinedIcon from "@mui/icons-material/AdminPanelSettingsOutlined";

/**
 * Navigation entries of the profile sidebar, grouped by section.
 * Sections with `adminOnly` are shown only to administrators.
 */
export const PROFILE_SIDEBAR = [
  {
    key: "account",
    label: "Cuenta",
    links: [
      {
        key: "profile",
        label: "Mi perfil",
        href: "/app/profile",
        Icon: PersonOutlineIcon,
      },
      {
        key: "manageAccount",
        label: "Gestionar cuenta",
        href: "/app/profile/account",
        Icon: ManageAccountsOutlinedIcon,
      },
    ],
  },
  {
    key: "projects",
    label: "Proyectos",
    links: [
      {
        key: "projects",
        label: "Mis proyectos",
        href: "/app/profile/projects",
        Icon: FolderOutlinedIcon,
      },
      {
        key: "requests",
        label: "Mis solicitudes",
        href: "/app/profile/requests",
        Icon: AssignmentOutlinedIcon,
      },
    ],
  },
  {
    key: "admin",
    label: "Administración",
    adminOnly: true,
    links: [
      {
        key: "manageUsers",
        label: "Usuarios",
        href: "/app/admin/users",
        Icon: PeopleOutlineIcon,
      },
      {
        key: "manageProjects",
        label: "Proyectos",
        href: "/app/admin/projects",
        Icon: FolderSharedOutlinedIcon,
      },
      {
        key: "manageRequests",
        label: "Solicitudes",
        href: "/app/admin/requests",
        Icon: FactCheckOutlinedIcon,
      },
      {
        key: "manageRoles",
        label: "Roles y permisos",
        href: "/app/admin/roles",
        Icon: AdminPanelSettingsOutlinedIcon,
      },
    ],
  },
];
