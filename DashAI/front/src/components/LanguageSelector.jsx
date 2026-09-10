import React from "react";
import { useTranslation } from "react-i18next";
import { FormControl, Select, MenuItem, Box } from "@mui/material";

export default function LanguageSelector() {
  const { i18n } = useTranslation();
  const currentLang = i18n.language.split("-")[0];

  const handleLanguageChange = (event) => {
    i18n.changeLanguage(event.target.value);
  };

  return (
    <FormControl size="small" sx={{ minWidth: 120 }}>
      <Select
        value={currentLang}
        onChange={handleLanguageChange}
        displayEmpty
        sx={{
          height: 32,
          "& .MuiSelect-select": {
            display: "flex",
            alignItems: "center",
            gap: 2,
          },
        }}
      >
        <MenuItem value="es">
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <span>🇨🇱</span>
            <span>Español</span>
          </Box>
        </MenuItem>
        <MenuItem value="en">
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <span>🇺🇸</span>
            <span>English</span>
          </Box>
        </MenuItem>
        <MenuItem value="pt">
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <span>🇧🇷</span>
            <span>Português</span>
          </Box>
        </MenuItem>
        <MenuItem value="de">
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <span>🇩🇪</span>
            <span>Deutsch</span>
          </Box>
        </MenuItem>
        <MenuItem value="zh">
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <span>🇨🇳</span>
            <span>中文</span>
          </Box>
        </MenuItem>
      </Select>
    </FormControl>
  );
}
