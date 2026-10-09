import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { Box, Grid, Button, Alert, AlertTitle, Skeleton } from "@mui/material";

function useContainerColumns(ref) {
  const [size, setSize] = useState(4);
  useEffect(() => {
    if (!ref.current) return;
    const observer = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      if (w >= 800) setSize(4);
      else if (w >= 500) setSize(6);
      else setSize(12);
    });
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [ref]);
  return size;
}
import SearchBar from "./SearchBar";
import CustomLayout from "../custom/CustomLayout";
import OptionBox from "./OptionBox";
import { useTranslation } from "react-i18next";

export default function SelectOptionMenu({
  goToPrevStep = null,
  title,
  subtitle,
  options,
  loading = false,
  searchBar = false,
  showNoDatasetAlert = false,
  onGoToDatasets = null,
  goToNextStep = null,
  dataTour = null,
  dataTourTarget = null,
}) {
  const [search, setSearch] = useState("");
  const filteredOptions = options.filter((option) =>
    option.name.toLowerCase().includes(search.toLowerCase()),
  );
  const { t } = useTranslation(["common", "datasets"]);
  const gridRef = useRef(null);
  const colSize = useContainerColumns(gridRef);

  // Cards share a single dynamic height, sized to fit whichever card's
  // content needs the most space, so text never gets cut off. Each OptionBox
  // measures its own natural (unconstrained) height and reports it here.
  const [cardHeights, setCardHeights] = useState({});
  const visibleNames = useMemo(
    () => filteredOptions.map((option) => option.name).join("|"),
    [filteredOptions],
  );
  useEffect(() => {
    setCardHeights({});
  }, [visibleNames]);
  const handleMeasure = useCallback((name, height) => {
    setCardHeights((prev) =>
      prev[name] === height ? prev : { ...prev, [name]: height },
    );
  }, []);
  const cardHeightValues = Object.values(cardHeights);
  const cardHeight = cardHeightValues.length
    ? Math.max(...cardHeightValues)
    : null;

  return (
    <CustomLayout title={title} subtitle={subtitle} padding={0}>
      <Box
        display={"flex"}
        height={"100%"}
        width={"100%"}
        flexDirection={"column"}
        justifyContent={"flex-start"}
      >
        {showNoDatasetAlert && (
          <Alert severity="warning" sx={{ mb: 4 }}>
            <AlertTitle>{t("datasets:label.noDatasetsAvailable")}</AlertTitle>
            {t("datasets:label.uploadDatasetBeforeCreatingSession")}
            {onGoToDatasets && (
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  size="small"
                  onClick={onGoToDatasets}
                >
                  {t("datasets:button.goToDatasets")}
                </Button>
              </Box>
            )}
          </Alert>
        )}

        {searchBar && (
          <Box width={"450px"}>
            <SearchBar
              placeholder={t("common:searchPlaceholder", "Search ...")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </Box>
        )}

        <Grid
          ref={gridRef}
          container
          direction="row"
          alignItems="stretch"
          spacing={2}
          sx={{ mt: 4, mx: 0, maxWidth: "100%" }}
        >
          {loading
            ? Array.from({ length: 6 }).map((_, index) => (
                <Grid size={colSize} key={index}>
                  <Skeleton variant="rounded" height={100} />
                </Grid>
              ))
            : null}
          {!loading &&
            filteredOptions.map((option, index) => {
              const { name, display_name, description, Icon, ...otherProps } =
                option;

              return (
                <Grid size={colSize} key={index}>
                  <OptionBox
                    optionName={display_name}
                    description={description}
                    onClick={() => goToNextStep(option.name)}
                    Icon={Icon}
                    minHeight={cardHeight}
                    onMeasure={(height) => handleMeasure(option.name, height)}
                    dataTour={
                      dataTour && dataTourTarget && name === dataTourTarget
                        ? dataTour
                        : dataTour && !dataTourTarget
                          ? dataTour
                          : undefined
                    }
                    {...otherProps}
                  />
                </Grid>
              );
            })}
        </Grid>
      </Box>

      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-end",
          mt: 4,
        }}
      >
        {goToPrevStep && (
          <Button variant="outlined" onClick={goToPrevStep}>
            {t("common:back")}
          </Button>
        )}
      </Box>
    </CustomLayout>
  );
}
