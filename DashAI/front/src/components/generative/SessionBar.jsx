import { Box, Typography, Divider } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useNavigate } from "react-router-dom";
import FolderIcon from "@mui/icons-material/Folder";
import ViewModuleIcon from "@mui/icons-material/ViewModule";
import SearchBar from "../threeSectionLayout/SearchBar";
import { useEffect, useMemo, useState } from "react";
import InfoSessionModal from "./InfoSessionModal";
import GroupedCollapsibleList from "../threeSectionLayout/GroupedCollapsibleList";
import Footer from "../threeSectionLayout/Footer";
import NewItemButton from "../threeSectionLayout/NewItemButton";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import { useTranslation } from "react-i18next";
import { useGenerative } from "./GenerativeContext";
import { standaloneRouteFor } from "./standaloneEntryPoints";

/**
 * The generative module's session list.
 *
 * @param {object} props
 * @param {Function} [props.onToggle] - Collapses the panel.
 * @param {Array} [props.sessions] - Overrides the sessions from context.
 * @param {number} [props.selectedSessionId] - Overrides the current selection.
 * @param {Function} [props.handleSessionClick] - Overrides click behaviour.
 * @param {Function} [props.handleNewSessionButton] - Overrides the new-session action.
 * @param {Function} [props.handleSessionDelete] - Overrides delete behaviour.
 * @param {boolean} [props.showSearch=true] - Whether to show the search field.
 * @param {string} [props.title] - Heading for the list. Defaults to the module
 *   name; a view scoped to one task passes that task's display name.
 * @returns {JSX.Element} The session sidebar.
 */
export default function SessionBar({
  onToggle,
  sessions: sessionsProp,
  selectedSessionId: selectedSessionIdProp,
  handleSessionClick: handleSessionClickProp,
  handleNewSessionButton: handleNewSessionButtonProp,
  handleSessionDelete: handleSessionDeleteProp,
  showSearch = true,
  title,
}) {
  const theme = useTheme();
  const navigate = useNavigate();
  const {
    tasks,
    sessions: sessionsCtx,
    selectedSessionId: selectedSessionIdCtx,
    deleteSessionById,
    deleteSessionsByIds,
    editSession,
    openSections,
    setOpenSections,
  } = useGenerative();

  const sessions = sessionsProp ?? sessionsCtx ?? [];
  const selectedSessionId = selectedSessionIdProp ?? selectedSessionIdCtx;
  const [searchQuery, setSearchQuery] = useState("");
  const [filteredSessions, setFilteredSessions] = useState(sessions);
  const [selectedInfoSession, setSelectedInfoSession] = useState(null);
  const { t } = useTranslation(["generative", "common"]);

  const SEARCH_THRESHOLD = 10;

  useEffect(() => {
    if (sessions.length <= SEARCH_THRESHOLD) setSearchQuery("");
  }, [sessions.length]);

  // Create a map of task_name to display_name for quick lookup
  const taskDisplayNameMap = useMemo(
    () =>
      tasks?.reduce((map, task) => {
        map[task.name] = task.display_name;
        return map;
      }, {}) || {},
    [tasks],
  );

  useEffect(() => {
    // Initialize all sections as closed based on unique task display names
    const uniqueDisplayNames = [
      ...new Set(
        sessions.map(
          (session) =>
            taskDisplayNameMap[session.task_name] || t("common:other"),
        ),
      ),
    ];
    setOpenSections((prev) => {
      const prevKeys = Object.keys(prev).sort().join(",");
      const newKeys = uniqueDisplayNames.slice().sort().join(",");
      if (prevKeys === newKeys) return prev;
      // Preserve existing open/close state; initialize new keys as closed
      const merged = {};
      uniqueDisplayNames.forEach((displayName) => {
        merged[displayName] = displayName in prev ? prev[displayName] : false;
      });
      return merged;
    });
  }, [sessions, tasks, taskDisplayNameMap, t]);

  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredSessions(sessions);
    } else {
      const filtered = sessions.filter((session) =>
        session.name.toLowerCase().includes(searchQuery.toLowerCase()),
      );
      setFilteredSessions(filtered);
    }
  }, [searchQuery, sessions]);

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  const handleSessionInfo = (id) => {
    // Find the session with the matching id
    const session = sessions.find((session) => session.id === id);
    if (session) {
      setSelectedInfoSession(session);
    }
  };

  const handleNewSessionButton = () => {
    if (handleNewSessionButtonProp) {
      handleNewSessionButtonProp();
      return;
    }
    navigate("/app/generative");
  };

  const handleSessionClick = (sessionId) => {
    const session = sessions.find((s) => s.id === sessionId);
    if (!session) return;

    if (handleSessionClickProp) {
      const displayName =
        taskDisplayNameMap[session.task_name] || t("common:other");
      handleSessionClickProp(sessionId, session.task_name, displayName);
      return;
    }

    const standaloneRoute = standaloneRouteFor(session.task_name);
    navigate(
      standaloneRoute
        ? `${standaloneRoute}/sessions/${sessionId}`
        : `/app/generative/sessions/${sessionId}`,
    );
  };

  const handleSessionDelete = async (id) => {
    if (handleSessionDeleteProp) {
      await handleSessionDeleteProp(id);
      return;
    }
    const wasSelected = id === selectedSessionId;
    const ok = await deleteSessionById(id);
    if (ok && wasSelected) {
      navigate("/app/generative");
    }
  };

  const getSessionDeleteConfirmationContent = (session) =>
    t(
      "generative:label.confirmDeleteSession",
      'Are you sure you want to delete the session "{{name}}"? This action cannot be undone.',
      { name: session.name },
    );

  const getSessionBulkDeleteConfirmationContent = (count) =>
    t("generative:label.confirmBulkDeleteSessions", {
      count,
      defaultValue:
        "Are you sure you want to delete the {{count}} selected sessions? This action cannot be undone.",
    });

  const handleBulkSessionDelete = async (ids) => {
    const idSet = new Set(ids);
    const wasSelected = idSet.has(selectedSessionId);
    const ok = await deleteSessionsByIds(ids);
    if (ok && wasSelected) {
      navigate("/app/generative");
    }
    return ok;
  };

  // Group sessions by task display_name, sorted to maintain a consistent order.
  // Memoized so the object identity stays stable across renders that don't
  // change the underlying data — GroupedCollapsibleList uses `groups` as an
  // effect dependency, so a fresh literal every render would re-run it.
  const sortedGroupedSessions = useMemo(() => {
    const groupedSessions = filteredSessions?.reduce((groups, session) => {
      // Get the display name from the task using the session's task_name
      const displayName =
        taskDisplayNameMap[session.task_name] || t("common:other");

      if (!groups[displayName]) {
        groups[displayName] = [];
      }
      groups[displayName].push(session);
      return groups;
    }, {});

    return groupedSessions
      ? Object.keys(groupedSessions)
          .sort()
          .reduce((sorted, key) => {
            sorted[key] = groupedSessions[key];
            return sorted;
          }, {})
      : {};
  }, [filteredSessions, taskDisplayNameMap, t]);

  return (
    <SideBar>
      <Box
        display="flex"
        flexDirection="column"
        flex={1}
        justifyContent={"flex-start"}
        minHeight={0}
      >
        <Box
          p={4}
          sx={{ height: "64px", display: "flex", alignItems: "center" }}
        >
          {/* Create new session button */}
          {selectedSessionId ? (
            <NewItemButton
              onClick={handleNewSessionButton}
              title={t("generative:button.generativeHub")}
              EndIcon={ViewModuleIcon}
            />
          ) : (
            <Typography variant="body1" color="textSecondary">
              {t("generative:label.generativeModule")}
            </Typography>
          )}
        </Box>

        {/* Search Bar */}
        {showSearch && sessions.length > SEARCH_THRESHOLD && (
          <Box px={2} pb={2} flex={"0 0 auto"}>
            <SearchBar
              placeholder={t("generative:label.searchSessions")}
              value={searchQuery}
              onChange={handleSearchChange}
            />
          </Box>
        )}

        <Divider sx={{ width: "90%", bgcolor: "divider", mx: "auto" }} />

        {/* Sessions */}
        <GroupedCollapsibleList
          groups={sortedGroupedSessions}
          selectedItemId={selectedSessionId}
          onItemClick={handleSessionClick}
          onItemDelete={handleSessionDelete}
          onItemEdit={editSession}
          onItemInfo={handleSessionInfo}
          title={title ?? t("common:generative")}
          Icon={FolderIcon}
          openGroups={openSections}
          onOpenGroupsChange={setOpenSections}
          getItemDescription={(session) => session.model_name}
          getDeleteConfirmationContent={getSessionDeleteConfirmationContent}
          onBulkDelete={handleBulkSessionDelete}
          selectItemsTooltip={t(
            "generative:label.selectSessionsToDelete",
            "Select sessions to delete",
          )}
          getBulkDeleteConfirmationContent={
            getSessionBulkDeleteConfirmationContent
          }
        />
      </Box>

      {/* Footer */}
      <Footer />
      {/* Session Info Modal */}
      {selectedInfoSession && (
        <InfoSessionModal
          sessionData={selectedInfoSession}
          open={!!selectedInfoSession}
          onClose={() => setSelectedInfoSession(null)}
        />
      )}
    </SideBar>
  );
}
