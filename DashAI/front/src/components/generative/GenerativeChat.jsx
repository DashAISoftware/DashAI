import { Box, Button, Divider, IconButton, Typography } from "@mui/material";
import InfoIcon from "@mui/icons-material/Info";
import ArrowRightAltIcon from "@mui/icons-material/ArrowRightAlt";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import { ChatBubble } from "./ChatBubble";
import {
  getProcessById,
  getProcessesBySessionId,
  deleteProcessById,
} from "../../api/process";
import { useState, useEffect, useRef, useMemo } from "react";
import { postProcess } from "../../api/process";
import { enqueueGenerativeProcessJob } from "../../api/job";
import { startJobQueue } from "../../api/job";
import { getHistoryBySessionId, getSessionById } from "../../api/session";
import {
  getComponentById,
  getComponentDownloadStatus,
} from "../../api/component";
import { getRelatedComponents } from "../../api/generativeTask";
import InfoSessionModal from "./InfoSessionModal";
import ModelSwitcher from "./ModelSwitcher";
import ComponentDownloadControl, {
  useComponentDownloadState,
} from "../models/model/ComponentDownloadControl";
import CredentialsDialog from "../credentials/CredentialsDialog";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../credentials/credentialStatus";
import VpnKeyOutlinedIcon from "@mui/icons-material/VpnKeyOutlined";
import { useSnackbar } from "notistack";
import { MediaInput } from "./MediaInput";
import JobQueueWidget from "../jobs/JobQueueWidget";
import { getRunStatus } from "../../utils/runStatus";
import TemplateModal from "../custom/TemplateModal";
import SourcesDisplay from "./SourcesDisplay";
import RAGBreadcrumbs from "./RAG/RAGBreadcrumbs";
import { Trans, useTranslation } from "react-i18next";
import { useGenerative } from "./GenerativeContext";
import { useTourContext } from "../tour/TourProvider";
import { useTheme } from "@mui/material/styles";

/**
 * The conversation view, shared by every generative task.
 *
 * @param {object} props
 * @param {object} [props.indexStatus] - For RAG sessions, the backend-reported
 *   indexing state. When documents are not indexed yet, the first answer also
 *   pays for indexing, so the waiting state says so instead of looking stuck.
 * @returns {JSX.Element} The chat.
 */
export default function GenerativeChat({ indexStatus }) {
  const theme = useTheme();

  const {
    selectedSessionId: sessionId,
    selectedTaskName: taskName,
    tasks,
    paramsVersion,
    setParamsVersion,
    fetchSessions,
  } = useGenerative();

  const inputsCardinality = useMemo(() => {
    const task = tasks?.find((t) => t.name === taskName);
    return task?.metadata?.inputs ?? { str: 1 };
  }, [tasks, taskName]);

  const [history, setHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [messagesWithHistory, setMessagesWithHistory] = useState([]);
  const [isLoadingMessage, setIsLoadingMessage] = useState(false);
  const chatContainerRef = useRef(null);
  const isAtBottomRef = useRef(true);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [sessionInfoVisible, setSessionInfoVisible] = useState(false);
  const [referenceModalOpen, setReferenceModalOpen] = useState(false);
  const [selectedReferenceText, setSelectedReferenceText] = useState("");
  const [referenceModalTitle, setReferenceModalTitle] = useState("");
  const [modelComponent, setModelComponent] = useState(null);
  const [modelsByName, setModelsByName] = useState({});
  const [credentialsDialogOpen, setCredentialsDialogOpen] = useState(false);
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["generative", "credentials"]);
  const tourContext = useTourContext();
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  const scrollToBottom = (force = false) => {
    const el = chatContainerRef.current;
    if (!el) return;

    // Force on new message; otherwise only follow if user is already near
    // the bottom, so polling updates don't yank the view down mid read.
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    if (force || distanceFromBottom <= 100) {
      el.scrollTop = el.scrollHeight;
    }
  };

  const isAtBottom = () => {
    if (!chatContainerRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    return Math.abs(scrollHeight - clientHeight - scrollTop) < 5; // 5px threshold
  };

  const handleOpenReference = (ref, key) => {
    const title = `Document ${ref.document_id}${
      ref.document_name ? ` (${ref.document_name})` : ""
    }${ref.document_position ? ` - Chunk ${ref.document_position}` : ""}`;
    setReferenceModalTitle(title);
    // Convert escaped newlines to actual newlines
    setSelectedReferenceText(ref.text.replace(/\\n/g, "\n"));
    setReferenceModalOpen(true);
  };

  const handleScroll = () => {
    const el = chatContainerRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    // Remember the user's position before any content change repaints, so the
    // scroll effect can decide whether to follow without re measuring stale.
    isAtBottomRef.current = distanceFromBottom <= 100;
    setShowScrollButton(distanceFromBottom > 100);
  };

  const getSessionInfo = () => {
    getSessionById(sessionId).then((response) => {
      setSessionInfo(response);
    });
  };

  // Resolve the session model's metadata plus a reconciled download status, so
  // the chat can block input and offer a download when the weights are missing
  // (e.g. after switching to a not downloaded model or deleting its download).
  const modelName = sessionInfo?.model_name;
  const refreshModelStatus = () => {
    if (!modelName) {
      setModelComponent(null);
      return;
    }
    Promise.all([
      getComponentById(modelName),
      getComponentDownloadStatus(modelName),
    ])
      .then(([component, status]) => {
        setModelComponent({ ...component, downloaded: status.downloaded });
      })
      .catch(() => setModelComponent(null));
  };

  useEffect(() => {
    refreshModelStatus();
  }, [modelName, paramsVersion]);

  // Map component name -> display name for the task's models, used to render
  // model change history events with friendly names instead of class names.
  useEffect(() => {
    const currentTaskName = sessionInfo?.task_name;
    if (!currentTaskName) return;
    getRelatedComponents(currentTaskName)
      .then((components) => {
        const map = {};
        (components || []).forEach((c) => {
          map[c.name] = c.display_name || c.name;
        });
        setModelsByName(map);
      })
      .catch(() => setModelsByName({}));
  }, [sessionInfo?.task_name]);

  // Use the live download state so an in-progress download keeps the input
  // blocked even when the backend already reports the (partial) files as
  // present, and unblocks the moment the download actually finishes.
  const { downloaded: liveDownloaded, downloading: liveDownloading } =
    useComponentDownloadState(modelComponent || { name: modelName || "" });
  // A model is usable only when its required credentials are authenticated AND
  // its weights are present. Credentials gate first: the download itself is
  // blocked until they are satisfied (see ComponentDownloadControl).
  const { statuses: credentialStatuses, loaded: credentialsLoaded } =
    useCredentialStatuses();
  const { locked: credentialsLocked, requiredPlatforms } =
    getComponentCredentialState(
      modelComponent || {},
      credentialStatuses,
      credentialsLoaded,
    );
  const downloadNeeded =
    Boolean(modelComponent?.metadata?.requires_download) &&
    !(liveDownloaded && !liveDownloading);
  const modelBlocked =
    Boolean(modelComponent) && (credentialsLocked || downloadNeeded);

  const getMessages = () => {
    getProcessesBySessionId(sessionId).then((response) => {
      console.log("Fetched messages:", response); // Add here
      setIsLoadingMessage(false);
      setMessages(response);
    });
  };

  const getHistory = () => {
    getHistoryBySessionId(sessionId).then((response) => {
      setHistory(response);
    });
  };

  const handleSendMessage = (input) => {
    setIsLoadingMessage(true);
    setShouldAutoScroll(true); // Enable auto-scroll when sending new message

    postProcess(sessionId, input).then((response) => {
      // Add the new message to the chat
      setMessages((prevMessages) => [...prevMessages, response]);

      // Enqueue the generative process job
      enqueueGenerativeProcessJob(response.id).then(() => {
        startJobQueue(true).then(() => {
          setIsLoadingMessage(false);
        });
      });

      // End tour if on final step
      if (tourContext?.run && tourContext?.stepIndex === 8) {
        setTimeout(() => {
          tourContext.stopTour();
        }, 100);
      }
    });
  };

  useEffect(() => {
    getMessages();
    getSessionInfo();
    getHistory();
  }, [sessionId, paramsVersion]);

  useEffect(() => {
    setMessages([]);
  }, [taskName]);

  const prevMessageCountRef = useRef(0);
  useEffect(() => {
    const isNewMessage =
      messagesWithHistory.length > prevMessageCountRef.current;
    prevMessageCountRef.current = messagesWithHistory.length;
    // Follow on a new message, or when the user was pinned to the bottom
    // before this update (e.g. the model reply replacing the waiting bubble).
    scrollToBottom(isNewMessage || isAtBottomRef.current);
  }, [messagesWithHistory]);

  useEffect(() => {
    if (messages.length === 0) return;

    const POLL_INTERVAL = 1500;

    const intervalId = setInterval(() => {
      const unfinished = messages.filter(
        (m) =>
          m.status !== 3 && // Not Finished
          m.status !== 4, // Not Error
      );

      if (unfinished.length === 0) {
        clearInterval(intervalId); // nothing left to poll
        return;
      }

      // Fetch latest status for each unfinished process
      unfinished.forEach((msg) => {
        getProcessById(msg.id).then((process) => {
          const status = process.status;

          // Error
          if (status === 4) {
            enqueueSnackbar(
              t("generative:error.processError", {
                error: process.output?.[0]?.data
                  ? `\n${process.output[0].data}`
                  : "",
              }),
              {
                autoHideDuration: 8000,
                style: { whiteSpace: "pre-line" },
              },
            );

            deleteProcessById(process.id).then(() => {
              setMessages((prev) => prev.filter((m) => m.id !== process.id));
            });
          } else {
            // Update progress or final result
            setMessages((prev) =>
              prev.map((m) => (m.id === process.id ? process : m)),
            );
          }
        });
      });
    }, POLL_INTERVAL);

    return () => clearInterval(intervalId); // cleanup
  }, [messages]);

  useEffect(() => {
    console.log("Combining messages and history for display"); // Add here
    console.log("Messages:", messages);
    console.log("TASK NAME:", taskName);
    console.log("session name:", sessionInfo?.name);
    console.log("session description:", sessionInfo?.description);
    let messagesObject = messages.map((process) => {
      // Check if there's reference data in the output (only for RAGTask)
      let referenceOutput = null;
      let mainOutput = process.output;

      if (
        taskName === "RAGTask" &&
        process.output &&
        process.output.length > 1
      ) {
        // Look for Dict type output that contains reference information
        const referenceItem = process.output.find(
          (item) => item.data_type === "Dict",
        );
        if (referenceItem) {
          console.log("Raw reference data:", referenceItem.data);
          try {
            // The data might be a Python dict string, try to parse it as JSON
            let dataStr = referenceItem.data;

            // If it starts with { but isn't valid JSON, it might be a Python dict
            // Try to convert Python dict format to JSON format
            if (dataStr.startsWith("{") && !dataStr.startsWith('{"')) {
              // Replace Python dict format with JSON format
              dataStr = dataStr
                .replace(/'/g, '"') // Replace single quotes with double quotes
                .replace(/True/g, "true") // Replace Python True with JSON true
                .replace(/False/g, "false") // Replace Python False with JSON false
                .replace(/None/g, "null"); // Replace Python None with JSON null
            }

            console.log("Processed data string:", dataStr);
            const parsedData = JSON.parse(dataStr);
            referenceOutput = parsedData;
            // Keep only non-Dict outputs as main output
            mainOutput = process.output.filter(
              (item) => item.data_type !== "Dict",
            );
          } catch (e) {
            console.log("Could not parse reference data:", e);
            console.log("Original data:", referenceItem.data);
            // If parsing fails, try to extract info using regex as fallback for multiple references
            try {
              // Updated regex to capture all fields: document_id, document_name, document_position, text
              const matches = [
                ...referenceItem.data.matchAll(
                  /(\d+):\s*\{\s*['"]?document_id['"]?\s*:\s*(\d+).*?['"]?document_name['"]?\s*:\s*['"]([^'"]*)['"]\s*.*?['"]?document_position['"]?\s*:\s*(\d+).*?['"]?text['"]?\s*:\s*['"]([^'"]*)['"]/gs,
                ),
              ];
              console.log("Regex matches for references:", matches);

              if (matches.length > 0) {
                referenceOutput = {};
                matches.forEach((match) => {
                  const refId = match[1];
                  referenceOutput[refId] = {
                    document_id: parseInt(match[2]),
                    document_name: match[3],
                    document_position: parseInt(match[4]),
                    text: match[5],
                  };
                });
                mainOutput = process.output.filter(
                  (item) => item.data_type !== "Dict",
                );
                console.log("Fallback parsing successful:", referenceOutput);
              }
            } catch (fallbackError) {
              console.log("Fallback parsing also failed:", fallbackError);
            }
          }
        }
      }

      return {
        type: "message",
        timestamp: process.created,
        id: process.id,
        input: process.input,
        output: mainOutput,
        referenceOutput: referenceOutput,
        status: process.status,
        end_time: process.end_time,
      };
    });

    let historyObject = history.map((entry) => {
      const isModelChange = entry.changes.some((c) => c.parameter === "model");
      return {
        type: "history",
        timestamp: entry.timestamp,
        id: entry.id,
        isModelChange,
        changedMessage: entry.changes.map((change) => {
          const isModel = change.parameter === "model";
          const label = isModel
            ? t("generative:label.sessionModel")
            : change.parameter;
          const oldValue = isModel
            ? modelsByName[change.oldValue] || change.oldValue
            : formatHistoryValue(change.oldValue);
          const newValue = isModel
            ? modelsByName[change.newValue] || change.newValue
            : formatHistoryValue(change.newValue);
          return (
            <span
              key={change.parameter}
              style={{
                display: "inline-flex",
                alignItems: "center",
                whiteSpace: "pre-wrap",
              }}
            >
              {label}: {oldValue} <ArrowRightAltIcon fontSize="small" />{" "}
              {newValue}{" "}
            </span>
          );
        }),
      };
    });

    let combinedMessages = [...messagesObject, ...historyObject];
    combinedMessages.sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp),
    );
    setMessagesWithHistory(combinedMessages);
  }, [messages, history]);

  const formatHistoryValue = (value) => {
    if (value === null || value === undefined) {
      return "";
    }

    if (typeof value === "string") {
      return value;
    }

    if (typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }

    if (typeof value === "object") {
      if (value.component) {
        return value.component;
      }

      try {
        return JSON.stringify(value);
      } catch (error) {
        return String(value);
      }
    }

    return String(value);
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      width={"100%"}
      height={"100%"}
      sx={{ overflow: "hidden", minHeight: 0 }}
    >
      {/* RAG Breadcrumbs - only show for RAG tasks */}
      {taskName === "RAGTask" && (
        <Box sx={{ width: "100%", px: 2, pt: 2 }}>
          <RAGBreadcrumbs sessionName={sessionInfo?.name} />
        </Box>
      )}

      {/* Model display */}
      <Box
        sx={{
          width: "100%",
          display: "flex",
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
          borderRadius: 1,
          my: 2,
          px: 1,
        }}
      >
        <Typography>
          {sessionInfo?.name ? sessionInfo.name : "Untitled Session"}{" "}
          {sessionInfo?.description ? ":" : null} {sessionInfo?.description}
        </Typography>

        {taskName !== "RAGTask" && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <ModelSwitcher
              sessionId={sessionId}
              taskName={sessionInfo?.task_name}
              currentModelName={sessionInfo?.model_name}
              onChanged={() => {
                getSessionInfo();
                fetchSessions();
                setParamsVersion((v) => v + 1);
              }}
            />
          </Box>
        )}
      </Box>

      <Divider sx={{ width: "100%", bgcolor: "divider" }} />

      {/* Chat display */}
      <Box
        sx={{
          position: "relative",
          display: "flex",
          flex: 1,
          minHeight: 0,
          width: "100%",
        }}
      >
        <Box
          display="flex"
          flexDirection="column"
          justifyContent="flex-start"
          alignItems="flex-start"
          gap={1}
          width={"100%"}
          flex={1}
          minHeight={0}
          overflow={"auto"}
          mt={1}
          p={2}
          ref={chatContainerRef}
          onScroll={handleScroll}
        >
          {messagesWithHistory?.map((message) => {
            return (
              <Box
                key={`${message.type}_${message.id}`}
                display="flex"
                flexDirection="column"
                justifyContent="flex-start"
                flexGrow={0}
                gap={1}
                width={"100%"}
                //height={"100%"}
                mt={1}
              >
                {message.type === "history" ? (
                  <Typography variant="body1" sx={{ opacity: 0.8 }}>
                    <Trans
                      i18nKey={
                        message.isModelChange
                          ? "generative:label.modelChangeEvent"
                          : "generative:label.parameterChangeEvent"
                      }
                    >
                      {message.isModelChange
                        ? "Model changed: "
                        : "Parameters updated: "}
                      <span>{message.changedMessage}</span>
                    </Trans>
                  </Typography>
                ) : (
                  <>
                    <ChatBubble
                      messages={message.input}
                      sender={"User"}
                      timestamp={new Date(
                        message.timestamp,
                      ).toLocaleTimeString()}
                      isUser={true}
                    />
                    {message.status === 3 ? (
                      <>
                        {taskName === "RAGTask" && message.referenceOutput ? (
                          // For RAG messages, we need custom layout to insert sources before timestamp
                          <>
                            <ChatBubble
                              messages={message.output}
                              sender={"Model"}
                              timestamp={null} // We'll handle timestamp separately
                            />
                            <SourcesDisplay
                              references={message.referenceOutput}
                              onOpenReference={handleOpenReference}
                              isUser={false}
                            />
                            {/* Add timestamp after sources with proper alignment */}
                            <Box
                              sx={{
                                ml: "40px", // Same alignment as sources and message content
                                mt: 1,
                                display: "flex",
                                justifyContent: "flex-start",
                              }}
                            >
                              <Box
                                sx={{
                                  fontSize: "0.75rem",
                                  color: "text.secondary",
                                  opacity: 0.7,
                                }}
                              >
                                {new Date(
                                  message.end_time,
                                ).toLocaleTimeString()}
                              </Box>
                            </Box>
                          </>
                        ) : (
                          // For non-RAG messages, use normal ChatBubble with timestamp
                          <ChatBubble
                            messages={message.output}
                            sender={"Model"}
                            timestamp={new Date(
                              message.end_time,
                            ).toLocaleTimeString()}
                          />
                        )}
                      </>
                    ) : (
                      <>
                        <ChatBubble isWaiting={true} sender="Model" />
                        {indexStatus && indexStatus.status !== "indexed" && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ ml: "40px" }}
                          >
                            {t("generative:rag.index.indexingInProgress")}
                          </Typography>
                        )}
                      </>
                    )}
                  </>
                )}
              </Box>
            );
          })}
        </Box>

        {showScrollButton && (
          <IconButton
            onClick={() => scrollToBottom(true)}
            sx={{
              position: "absolute",
              bottom: 16,
              right: 16,
              bgcolor: "background.paper",
              border: 1,
              borderColor: "divider",
              boxShadow: 2,
              "&:hover": { bgcolor: "background.paper" },
            }}
          >
            <KeyboardArrowDownIcon />
          </IconButton>
        )}
      </Box>

      {/* Chat input, or a download prompt when the model is not available */}
      {modelBlocked ? (
        <Box
          sx={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 1,
            p: 3,
            borderRadius: 1,
            border: 1,
            borderColor: "divider",
            bgcolor: "action.hover",
          }}
        >
          <Typography variant="body2" color="text.secondary">
            {credentialsLocked
              ? t("generative:label.modelRequiresCredentials", {
                  platform: requiredPlatforms,
                })
              : t("generative:label.modelNotDownloaded")}
          </Typography>
          {credentialsLocked ? (
            <Button
              size="small"
              variant="outlined"
              startIcon={<VpnKeyOutlinedIcon />}
              onClick={() => setCredentialsDialogOpen(true)}
            >
              {t("credentials:manage")}
            </Button>
          ) : (
            <ComponentDownloadControl
              component={modelComponent}
              onStatusChange={() => refreshModelStatus()}
            />
          )}
        </Box>
      ) : (
        <MediaInput
          key={sessionId}
          onSendMessage={(input) => {
            handleSendMessage(input);
          }}
          isLoading={isLoadingMessage}
          inputsCardinality={inputsCardinality}
        />
      )}

      {/* Session Info Modal */}
      {sessionInfo && (
        <InfoSessionModal
          sessionData={sessionInfo}
          open={sessionInfoVisible}
          onClose={() => setSessionInfoVisible(false)}
        />
      )}

      <CredentialsDialog
        open={credentialsDialogOpen}
        onClose={() => setCredentialsDialogOpen(false)}
      />
    </Box>
  );
}
