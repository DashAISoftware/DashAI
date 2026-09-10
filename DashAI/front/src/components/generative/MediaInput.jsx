import { useEffect, useState } from "react";
import { TextField, Button, Box } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import { useTranslation } from "react-i18next";
import {
  MEDIA_KINDS,
  MEDIA_ORDER,
  parseCardinality,
} from "./mediaInput/constants";
import { MediaPreviewList } from "./mediaInput/MediaPreviewList";
import { MediaAttachPopper } from "./mediaInput/MediaAttachPopper";
import { MediaOnlyPlaceholder } from "./mediaInput/MediaOnlyPlaceholder";
import { useMediaFiles } from "./mediaInput/useMediaFiles";
import { useTourContext } from "../tour/TourProvider";

export function MediaInput({
  onSendMessage,
  isLoading = false,
  inputsCardinality = { str: 1 },
}) {
  const { t } = useTranslation(["generative"]);
  const tourContext = useTourContext();
  const [menuOpen, setMenuOpen] = useState(false);
  const {
    text,
    setText,
    filesByKind,
    previewsByKind,
    fileInputRefs,
    wantsText,
    activeKinds,
    hasAnyMedia,
    handleFileChange,
    removeFile,
    requirementsMet,
    reset,
    collectPayload,
  } = useMediaFiles(inputsCardinality);

  const pickKind = (kind) => {
    setMenuOpen(false);
    fileInputRefs.current[kind]?.click();
  };

  const handleSend = () => {
    if (!requirementsMet) return;
    onSendMessage(collectPayload());
    reset();
    const currentTarget = tourContext?.steps?.[tourContext?.stepIndex]?.target;
    if (tourContext?.run && currentTarget === '[data-tour="chat-input"]') {
      tourContext.nextStep();
    }
  };

  useEffect(() => {
    if (wantsText || isLoading) return;
    const onKeyDown = (e) => {
      if (e.key !== "Enter" || e.shiftKey) return;
      const tag = e.target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      e.preventDefault();
      handleSend();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        gap: 2,
        flexShrink: 0,
      }}
    >
      <MediaPreviewList
        activeKinds={activeKinds}
        previewsByKind={previewsByKind}
        onRemove={removeFile}
      />

      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
        {wantsText ? (
          <TextField
            fullWidth
            multiline
            minRows={3}
            maxRows={3}
            placeholder={t("generative:label.typeYourMessage")}
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={isLoading}
            variant="outlined"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !isLoading) {
                e.preventDefault();
                handleSend();
              }
            }}
            data-tour="chat-input"
          />
        ) : (
          <MediaOnlyPlaceholder
            hasAnyMedia={hasAnyMedia}
            inputsCardinality={inputsCardinality}
            filesByKind={filesByKind}
            onPick={pickKind}
          />
        )}

        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            alignItems: "center",
            position: "relative",
          }}
        >
          {wantsText && (
            <MediaAttachPopper
              open={menuOpen}
              setOpen={setMenuOpen}
              disabled={isLoading || !hasAnyMedia}
              inputsCardinality={inputsCardinality}
              filesByKind={filesByKind}
              onPick={pickKind}
            />
          )}

          {MEDIA_ORDER.map((kind) => {
            const { accept } = MEDIA_KINDS[kind];
            const { max } = parseCardinality(inputsCardinality[kind]);
            return (
              <Box
                key={`file-input-${kind}`}
                component="input"
                type="file"
                accept={accept}
                multiple={max > 1}
                onChange={handleFileChange(kind)}
                disabled={isLoading}
                sx={{ display: "none" }}
                ref={(el) => {
                  fileInputRefs.current[kind] = el;
                }}
              />
            );
          })}
          <Button
            variant="contained"
            color="primary"
            onClick={handleSend}
            disabled={isLoading || !requirementsMet}
            sx={{ minWidth: 40, width: 40, height: 40, padding: 0 }}
          >
            <SendIcon />
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
