import PropTypes from "prop-types";
import {
  Box,
  Chip,
  LinearProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";

function formatNumber(value, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }

  const number = Number(value);
  if (Math.abs(number) >= 100) return number.toFixed(1);
  if (Math.abs(number) >= 10) return number.toFixed(2);
  return number.toFixed(digits);
}

function Section({ title, children }) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      <Typography variant="subtitle1" fontWeight={700}>
        {title}
      </Typography>
      {children}
    </Box>
  );
}

function SummaryCard({ label, value, helper }) {
  const theme = useTheme();

  return (
    <Box
      sx={{
        flex: "1 1 180px",
        minWidth: 180,
        p: 2,
        border: 1,
        borderColor: theme.palette.divider,
        borderRadius: 1,
        bgcolor: theme.palette.background.paper,
      }}
    >
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h6" sx={{ mt: 0.5 }}>
        {value}
      </Typography>
      {helper && (
        <Typography variant="caption" color="text.secondary">
          {helper}
        </Typography>
      )}
    </Box>
  );
}

function ClusteringProfileVisualizer({ data, minimalist = false }) {
  const theme = useTheme();
  const clusterSizes = Object.entries(data.cluster_sizes || {}).sort(
    ([a], [b]) => Number(a) - Number(b),
  );
  const totalRows = clusterSizes.reduce(
    (acc, [, size]) => acc + Number(size),
    0,
  );
  const metrics = Object.entries(data.metrics || {});
  const profiles = [...(data.cluster_profiles || [])].sort(
    (a, b) => Number(a.cluster) - Number(b.cluster),
  );

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        minHeight: 0,
        overflowY: "auto",
        overflowX: "hidden",
        p: minimalist ? 1.5 : { xs: 2, md: 3 },
        display: "flex",
        flexDirection: "column",
        gap: minimalist ? 2 : 3,
        color: theme.palette.text.primary,
      }}
    >
      <Stack direction="row" gap={2} flexWrap="wrap">
        <SummaryCard
          label="Algoritmo"
          value={data.algorithm || "Desconocido"}
        />
        <SummaryCard label="Clusters" value={data.n_clusters ?? "-"} />
        <SummaryCard label="Filas agrupadas" value={totalRows || "-"} />
        {data.noise_info?.n_noise_points !== undefined && (
          <SummaryCard
            label="Puntos de ruido"
            value={data.noise_info.n_noise_points}
            helper="Filas marcadas como ruido por el algoritmo"
          />
        )}
      </Stack>

      {metrics.length > 0 && (
        <Section title="Métricas">
          <TableContainer
            sx={{
              border: 1,
              borderColor: theme.palette.divider,
              borderRadius: 1,
              bgcolor: theme.palette.background.paper,
            }}
          >
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Métrica</TableCell>
                  <TableCell align="right">Valor</TableCell>
                  <TableCell>Interpretación</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {metrics.map(([key, metric]) => (
                  <TableRow key={key} hover>
                    <TableCell sx={{ fontWeight: 600 }}>
                      {metric.label || key}
                    </TableCell>
                    <TableCell align="right">
                      {formatNumber(metric.value)}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {metric.interpretation || "-"}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Section>
      )}

      <Section title="Tamaño de Clusters">
        <TableContainer
          sx={{
            border: 1,
            borderColor: theme.palette.divider,
            borderRadius: 1,
            bgcolor: theme.palette.background.paper,
          }}
        >
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Cluster</TableCell>
                <TableCell align="right">Filas</TableCell>
                <TableCell align="right">Porcentaje</TableCell>
                <TableCell>Distribución</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {clusterSizes.map(([cluster, size]) => {
                const percent = totalRows
                  ? (Number(size) / totalRows) * 100
                  : 0;
                return (
                  <TableRow key={cluster} hover>
                    <TableCell sx={{ fontWeight: 600 }}>
                      Cluster {cluster}
                    </TableCell>
                    <TableCell align="right">{size}</TableCell>
                    <TableCell align="right">
                      {formatNumber(percent, 1)}%
                    </TableCell>
                    <TableCell sx={{ minWidth: 160 }}>
                      <LinearProgress
                        variant="determinate"
                        value={percent}
                        sx={{ height: 8, borderRadius: 1 }}
                      />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Section>

      <Section title="Características Descriptivas">
        <Typography variant="body2" color="text.secondary">
          Se muestran las variables cuyo promedio dentro del cluster se aleja
          más del promedio global. Ayudan a entender que hace reconocible a cada
          grupo.
        </Typography>
        <TableContainer
          sx={{
            border: 1,
            borderColor: theme.palette.divider,
            borderRadius: 1,
            bgcolor: theme.palette.background.paper,
          }}
        >
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Cluster</TableCell>
                <TableCell align="right">Tamaño</TableCell>
                <TableCell>Variables más descriptivas</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {profiles.map((profile) => (
                <TableRow key={profile.cluster} hover>
                  <TableCell sx={{ fontWeight: 700 }}>
                    Cluster {profile.cluster}
                  </TableCell>
                  <TableCell align="right">{profile.size}</TableCell>
                  <TableCell>
                    <Stack gap={1}>
                      {(profile.distinctive_features || []).map((feature) => (
                        <Box
                          key={`${profile.cluster}-${feature.feature}`}
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            flexWrap: "wrap",
                          }}
                        >
                          <Chip
                            label={feature.feature}
                            size="small"
                            variant="outlined"
                          />
                          <Typography variant="body2">
                            {feature.direction === "above average"
                              ? "más alto"
                              : "más bajo"}{" "}
                            que el promedio
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            promedio cluster{" "}
                            {formatNumber(feature.cluster_mean)} — global{" "}
                            {formatNumber(feature.global_mean)}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Section>

      {Object.keys(data.algorithm_extras || {}).length > 0 && (
        <Section title="Detalles del Algoritmo">
          <TableContainer
            sx={{
              border: 1,
              borderColor: theme.palette.divider,
              borderRadius: 1,
              bgcolor: theme.palette.background.paper,
            }}
          >
            <Table size="small">
              <TableBody>
                {Object.entries(data.algorithm_extras).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell sx={{ fontWeight: 600 }}>{key}</TableCell>
                    <TableCell align="right">{formatNumber(value)}</TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {key === "inertia"
                          ? "Menor indica clusters más compactos para la misma cantidad de clusters."
                          : "Detalle especifico del algoritmo utilizado."}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Section>
      )}
    </Box>
  );
}

Section.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

SummaryCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  helper: PropTypes.string,
};

ClusteringProfileVisualizer.propTypes = {
  data: PropTypes.object.isRequired,
  minimalist: PropTypes.bool,
};

export default ClusteringProfileVisualizer;
