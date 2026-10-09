import { Box, Paper, useTheme } from "@mui/material";
import { TextMessage } from "./TextMessage";
import { ImageMessage } from "./ImageMessage";
import { AudioMessage } from "./AudioMessage";
import { VideoMessage } from "./VideoMessage";
import LoadingDots from "../shared/LoadingDots";

export function MessageContent({ messages, isUser, isWaiting }) {
  const theme = useTheme();

  return (
    <Paper
      sx={{
        backgroundColor: theme.palette.ui.box,
        color: "text.primary",
        padding: theme.spacing(1.5, 4),
        maxWidth: "100%",
        borderRadius: 2,
        borderTopRightRadius: isUser ? 0 : "inherit",
        borderTopLeftRadius: isUser ? "inherit" : 0,
        position: "relative",
      }}
    >
      {isWaiting ? (
        <LoadingDots />
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {messages?.map((message) => {
            const type = message["data_type"];
            return (
              <Box key={message.id}>
                {type === "str" && <TextMessage message={message.data} />}
                {type === "Image" && <ImageMessage image={message.data} />}
                {type === "Audio" && <AudioMessage audio={message.data} />}
                {type === "Video" && <VideoMessage video={message.data} />}
              </Box>
            );
          })}
        </Box>
      )}
    </Paper>
  );
}
