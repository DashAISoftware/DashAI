import {
  Collapse,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";
import React, { useState } from "react";
import {
  DataObject as DataObjectIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIcon,
} from "@mui/icons-material";
import PropTypes from "prop-types";
/**
 * Recursive component that transforms the JSON of a configurable object into a nested and expandable list.
 * @param {string} name the name of the current parameter to render as an item
 * @param {object| bool | number| string} value the value of the curent item, it can be the value of the
 * parameter or an object with its own parameters.
 */
function ParameterListItem({ name, value }) {
  const [open, setOpen] = useState(name === "Parameters");

  // configurable object parameter case
  if (value && value.constructor.name === "Object") {
    return (
      <List key={name} dense>
        <ListItemButton onClick={() => setOpen((current) => !current)}>
          <ListItemIcon>
            <DataObjectIcon color="primary" />
          </ListItemIcon>
          <ListItemText>{name}</ListItemText>
          {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </ListItemButton>
        <Collapse in={open} timeout="auto" unmountOnExit>
          <List sx={{ pl: 4 }} dense>
            {Object.keys(value).map((paramName) => (
              <ParameterListItem
                key={`${name}-${paramName}`}
                name={paramName}
                value={value[paramName]}
              />
            ))}
          </List>
        </Collapse>
      </List>
    );
  }

  // simple key-value parameter case
  return (
    <ListItem>
      <ListItemText
        primary={<Typography variant="p">{name + ":"}</Typography>}
        secondary={
          <Typography variant="p" sx={{ ml: 1, color: "gray" }}>
            {value}
          </Typography>
        }
      />
    </ListItem>
  );
}

ParameterListItem.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
    PropTypes.bool,
    PropTypes.object,
    PropTypes.array,
  ]).isRequired,
};

export default ParameterListItem;
