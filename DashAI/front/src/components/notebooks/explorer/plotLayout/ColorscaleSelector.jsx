import { useState } from "react";
import {
  TextField,
  MenuItem,
  Button,
  Box,
  Card,
  CardContent,
  Stack,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  IconButton,
  Divider,
  FormControlLabel,
  Switch,
  alpha,
  Alert,
  useTheme,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import DebouncedColorPicker from "./DebouncedColorPicker";
import { useTranslation } from "react-i18next";

const COLORMAPS = [
  "Blackbody",
  "Bluered",
  "Blues",
  "Cividis",
  "Earth",
  "Electric",
  "Greens",
  "Greys",
  "Hot",
  "Jet",
  "Picnic",
  "Portland",
  "Rainbow",
  "RdBu",
  "Reds",
  "Viridis",
  "YlGnBu",
  "YlOrRd",
];

export default function ColorscaleSelector({
  value,
  onChange,
  reversed = false,
  onReversedChange = null,
}) {
  const theme = useTheme();
  const isArrayMode = Array.isArray(value);

  const [mode, setMode] = useState(isArrayMode ? "array" : "preset");
  const [localArray, setLocalArray] = useState(
    Array.isArray(value)
      ? value
      : [
          [0, "rgb(0,0,0)"],
          [1, "rgb(255,255,255)"],
        ],
  );
  const { t } = useTranslation(["datasets"]);

  const applyArrayChange = (updated) => {
    setLocalArray(updated);
    onChange(updated);
  };

  const handleArrayValueChange = (idx, newVal) => {
    const updated = [...localArray];
    updated[idx][0] = newVal;
    applyArrayChange(updated);
  };

  const handleArrayColorChange = (idx, newColor) => {
    const updated = [...localArray];
    updated[idx][1] = newColor;
    applyArrayChange(updated);
  };

  const addStop = () => {
    applyArrayChange([...localArray, [1, "rgb(255,255,255)"]]);
  };

  const removeStop = (i) => {
    applyArrayChange(localArray.filter((_, idx) => idx !== i));
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    if (newMode === "preset") {
      onChange(COLORMAPS[0] || "Viridis");
    } else {
      onChange(localArray);
    }
  };

  return (
    <Box
      sx={{
        bgcolor: theme.palette.ui.panelDark,
        p: 3,
        borderBottom: `1px solid ${theme.palette.ui.borderLight}`,
      }}
    >
      <Stack spacing={4}>
        <Box>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              mb: 2,
            }}
          >
            {t("datasets:label.colorscaleMode")}
          </Typography>
          <ToggleButtonGroup
            value={mode}
            exclusive
            onChange={(e, newMode) => {
              if (newMode !== null) switchMode(newMode);
            }}
            fullWidth
            size="small"
            sx={{
              "& .MuiToggleButton-root": {
                border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                fontWeight: 500,
                color: "text.secondary",
                "&.Mui-selected": {
                  backgroundColor: alpha(theme.palette.primary.main, 0.2),
                  color: theme.palette.primary.main,
                  borderColor: theme.palette.primary.main,
                },
              },
            }}
          >
            <ToggleButton value="preset">
              {t("datasets:label.presetScale")}
            </ToggleButton>
            <ToggleButton value="array">
              {t("datasets:label.customArray")}
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* Reversing is a property of the scale itself rather than of either
            mode, so it stays visible in both. Hiding it in array mode would
            leave a flag silently reversing a hand built set of stops. */}
        {onReversedChange && (
          <FormControlLabel
            sx={{ m: 0 }}
            control={
              <Switch
                size="small"
                checked={Boolean(reversed)}
                onChange={(event) => onReversedChange(event.target.checked)}
              />
            }
            label={
              <Typography variant="body2" color="text.secondary">
                {t("datasets:label.reverseColorscale")}
              </Typography>
            }
          />
        )}

        <Divider
          sx={{
            width: "100%",
            borderColor: theme.palette.ui.divider,
          }}
        />

        {mode === "preset" ? (
          /* -------- PRESET MODE ---------- */
          <Box>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                mb: 1,
              }}
            >
              {t("datasets:label.selectColorscale")}
            </Typography>
            <TextField
              select
              label={t("datasets:label.colorscale")}
              variant="outlined"
              size="small"
              value={typeof value === "string" ? value : ""}
              onChange={(e) => onChange(e.target.value)}
              fullWidth
              sx={{
                "& .MuiOutlinedInput-root": {
                  fontWeight: 500,
                  "& fieldset": {
                    borderColor: alpha(theme.palette.primary.main, 0.3),
                  },
                  "&:hover fieldset": {
                    borderColor: theme.palette.primary.main,
                  },
                  "&.Mui-focused fieldset": {
                    borderColor: theme.palette.primary.main,
                  },
                },
                "& .MuiOutlinedInput-input": {
                  color: "text.primary",
                },
                "& .MuiInputBase-input::placeholder": {
                  color: "text.secondary",
                  opacity: 1,
                },
              }}
            >
              {COLORMAPS.map((scale) => (
                <MenuItem key={scale} value={scale}>
                  {scale}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        ) : (
          /* -------- ARRAY MODE ---------- */
          <Box>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                mb: 1,
              }}
            >
              {t("datasets:label.colorStops")}
            </Typography>
            {localArray.length < 2 && (
              <Alert severity="warning" sx={{ mb: 4 }}>
                {t("datasets:label.atLeastTwoColorStopsRequired")}
              </Alert>
            )}
            {localArray.length >= 2 &&
              (localArray[0][0] !== 0 ||
                localArray[localArray.length - 1][0] !== 1) && (
                <Alert severity="warning" sx={{ mb: 4 }}>
                  {t("datasets:label.firstLastStopsAtExtremes")}
                </Alert>
              )}

            <Stack spacing={4}>
              {localArray.map((item, i) => (
                <Card
                  key={i}
                  variant="outlined"
                  sx={{
                    background: alpha(theme.palette.background.paper, 0.4),
                    border: `1px solid ${alpha(
                      theme.palette.primary.main,
                      0.15,
                    )}`,
                    transition: "all 0.2s ease",
                    "&:hover": {
                      border: `1px solid ${theme.palette.primary.main}`,
                      boxShadow: `0 2px 8px ${alpha(
                        theme.palette.primary.main,
                        0.15,
                      )}`,
                    },
                  }}
                >
                  <CardContent sx={{ p: 4, "&:last-child": { pb: 4 } }}>
                    <Stack
                      direction="row"
                      spacing={4}
                      alignItems="center"
                      sx={{ width: "100%" }}
                    >
                      {/* Stop Index Label */}
                      <Typography
                        variant="body1"
                        component="div"
                        sx={{
                          minWidth: 32,
                          height: 32,
                          borderRadius: "50%",
                          backgroundColor: alpha(
                            theme.palette.primary.main,
                            0.15,
                          ),
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontWeight: 600,
                          color: theme.palette.primary.main,
                        }}
                      >
                        {i + 1}
                      </Typography>

                      <TextField
                        label={t("datasets:label.position")}
                        type="number"
                        variant="outlined"
                        size="small"
                        slotProps={{
                          htmlInput: {
                            step: 0.1,
                            min: 0,
                            max: 1,
                          },
                        }}
                        value={item[0]}
                        onChange={(e) =>
                          handleArrayValueChange(i, parseFloat(e.target.value))
                        }
                        sx={{
                          width: 100,
                          "& .MuiOutlinedInput-root": {
                            "& fieldset": {
                              borderColor: alpha(
                                theme.palette.primary.main,
                                0.3,
                              ),
                            },
                            "&:hover fieldset": {
                              borderColor: theme.palette.primary.main,
                            },
                            "&.Mui-focused fieldset": {
                              borderColor: theme.palette.primary.main,
                            },
                          },
                        }}
                      />

                      <DebouncedColorPicker
                        label={t("datasets:label.color")}
                        value={item[1]}
                        onChange={(color) => handleArrayColorChange(i, color)}
                      />

                      <Box sx={{ flex: 1 }} />

                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => removeStop(i)}
                        sx={{
                          "&:hover": {
                            backgroundColor: alpha(
                              theme.palette.error.main,
                              0.1,
                            ),
                          },
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </CardContent>
                </Card>
              ))}

              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={addStop}
                size="small"
                sx={{
                  textTransform: "none",
                  fontWeight: 500,
                  borderStyle: "dashed",
                  borderColor: alpha(theme.palette.primary.main, 0.4),
                  color: theme.palette.primary.main,
                  "&:hover": {
                    borderStyle: "dashed",
                    backgroundColor: alpha(theme.palette.primary.main, 0.08),
                    borderColor: theme.palette.primary.main,
                  },
                }}
              >
                {t("datasets:button.addColorStop")}
              </Button>
            </Stack>
          </Box>
        )}
      </Stack>
    </Box>
  );
}
