import { TextField } from "@mui/material";
import { styled } from "@mui/material/styles";

export const Input = styled(TextField)(({ theme }) => ({
  width: "20vw",
  ".MuiFormHelperText-root": {
    height: 48,
  },
}));
