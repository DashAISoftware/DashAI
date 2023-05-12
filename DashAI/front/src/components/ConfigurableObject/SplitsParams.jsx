import React from "react";
import {
  Dialog,
  Button,
  Typography,
  DialogTitle,
  DialogContent,
} from "@mui/material";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { ErrorMessageDiv } from "../../styles/globalComponents";
import ParameterForm from "./ParameterForm";
import PropTypes from "prop-types";
import * as S from "../../styles/components/DatasetConfigStyles";
/**
 * This component is used to render the configuration for splits in a dataloader configuration
 * If the JSON schema of dataloader have split configuration
  this section is showed. This component shows the parameters
  in a div section that can be hidden because it's depends if
  the user have the splits defined before or want to do it now,
  so a parameter control if this section is showed or not.

  Also, this section have an option of 'more options' that is
  showed only if the JSON schema have it. This is for advanced
  settings like set a seed, or shuffle the data.
 * @param {object} paramsSchema JSON object that describes a configurable object
 * @param {function} onSubmit function to submit the parameters of the dataloader
 * @param {bool} showSplitConfig shows or hides the split section, depending on user input
 * @param {bool} showMoreOptions
 * @param {function} setShowMoreOptions function to change the state of showMoreOptions
 * @param {bool} showSplitsError
 */
function SplitsParams({
  paramsSchema,
  onSubmit,
  showSplitConfig,
  showMoreOptions,
  setShowMoreOptions,
  showSplitsError,
}) {
  let hideSection = showSplitConfig;

  if (showSplitConfig === "True") {
    hideSection = true;
  }

  if (showSplitConfig === "False") {
    hideSection = false;
  }

  return (
    <div>
      {/* splits configuration form that can be hidden or shown as needed. */}
      <S.HiddenSection style={{ maxHeight: !hideSection ? "500px" : "0px" }}>
        <hr />
        <Typography variant="p">Splits configuration</Typography>
        {showSplitsError ? (
          <ErrorMessageDiv>The size of splits must sum to 1.</ErrorMessageDiv>
        ) : null}
        <ParameterForm
          parameterSchema={paramsSchema}
          onFormSubmit={(values) => onSubmit("splits", values)}
        />
        {paramsSchema.more_options !== undefined ? (
          <Button
            startIcon={<ArrowDropDownIcon />}
            onClick={() => {
              setShowMoreOptions(true);
            }}
          >
            More Options
          </Button>
        ) : null}
      </S.HiddenSection>

      {/* Modal to show form for additional/advanced configuration */}
      {showMoreOptions ? (
        <Dialog
          open={showMoreOptions}
          onClose={() => setShowMoreOptions(false)}
        >
          <DialogTitle>Advanced configuration</DialogTitle>
          <DialogContent>
            <ParameterForm
              parameterSchema={paramsSchema.more_options}
              onFormSubmit={(values) => onSubmit("Advanced", values)}
              submitButton
            />
          </DialogContent>
        </Dialog>
      ) : null}
    </div>
  );
}

SplitsParams.propTypes = {
  paramsSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  onSubmit: PropTypes.func.isRequired,
  showSplitConfig: PropTypes.bool.isRequired,
  showMoreOptions: PropTypes.bool.isRequired,
  setShowMoreOptions: PropTypes.func.isRequired,
  showSplitsError: PropTypes.bool.isRequired,
};

export default SplitsParams;