import { memo } from "react";
import { Box, Typography } from "@mui/material";
import { ChatAvatar } from "./ChatAvatar";
import { ChatTimestamp } from "./ChatTimeStamp";
import { MessageContent } from "./MessageContent";

function ChatBubbleComponent({
  messages,
  sender = "",
  timestamp = null,
  isUser = false,
  isWaiting = false,
}) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        alignItems: "flex-start",
        justifyContent: isUser ? "flex-end" : "flex-start",
        mb: 4,
        width: "100%",
      }}
    >
      {!isUser && <ChatAvatar isUser={isUser} alt={sender || undefined} />}

      <Box sx={{ maxWidth: "80%" }}>
        {!isUser && sender && (
          <Typography
            variant="body2"
            component="span"
            sx={{
              ml: 2,
              mb: 1,
              display: "block",
              color: "text.secondary",
            }}
          >
            {sender}
          </Typography>
        )}

        <MessageContent
          messages={messages}
          isUser={isUser}
          isWaiting={isWaiting}
        />

        <ChatTimestamp timestamp={timestamp} isUser={isUser} />
      </Box>

      {isUser && <ChatAvatar isUser={isUser} />}
    </Box>
  );
}

export const ChatBubble = memo(ChatBubbleComponent);
