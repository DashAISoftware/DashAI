import React, { useState } from "react";
import { Box, Typography, CardContent, Button } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import TitleIcon from "@mui/icons-material/Title";
import {
  ResponsiveContainer,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { StatBox } from "../StatBox";
import ExportableCard from "../ExportableCard";
import { useTranslation } from "react-i18next";

const BATCH_SIZE = 10;

export const CategoricalTab = ({ categoricalStats }) => {
  const { t } = useTranslation(["datasets", "common"]);
  const theme = useTheme();
  const [activeIndices, setActiveIndices] = useState({});
  const entries = Object.entries(categoricalStats ?? {});
  const [visibleCount, setVisibleCount] = useState(BATCH_SIZE);
  const visibleEntries = entries.slice(0, visibleCount);
  const remaining = entries.length - visibleCount;

  return (
    <Box display="flex" flexDirection="column" gap={8}>
      {visibleEntries.map(([column, stats]) => (
        <ExportableCard
          key={column}
          filename={`categorical_${column}`}
          exportData={{ column, ...stats }}
          sx={{ borderRadius: 2 }}
        >
          <CardContent sx={{ bgcolor: theme.palette.ui.box }}>
            {/* Header */}
            <Box display="flex" alignItems="center" mb={4}>
              <TitleIcon sx={{ color: "primary.main", mr: 2 }} />
              <Typography variant="h6" fontWeight="bold">
                {column}
              </Typography>
            </Box>

            {/* Summary Stats */}
            <Box display="flex" flexWrap="wrap" gap={4} mb={8}>
              <Box flex="1 1 300px" minWidth="250px">
                <StatBox
                  label={t("datasets:label.uniqueValues")}
                  value={stats.n_unique}
                />
              </Box>
              <Box flex="1 1 300px" minWidth="250px">
                <StatBox
                  label={t("datasets:label.mostFrequent")}
                  value={stats.most_frequent}
                />
              </Box>
              <Box flex="1 1 300px" minWidth="250px">
                <StatBox
                  label={t("datasets:label.topValueCount")}
                  value={stats.most_frequent_count}
                />
              </Box>
            </Box>

            {/* Charts */}
            <Box display="flex" flexWrap="wrap" gap={8}>
              {/* Value Distribution */}
              <Box flex="1 1 400px" minWidth="300px">
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                >
                  {t("datasets:label.valueDistribution")}
                </Typography>
                <Box sx={{ width: "100%", height: 250 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stats.top_5}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="value"
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis />
                      <Tooltip
                        cursor={false}
                        contentStyle={{
                          backgroundColor: theme.palette.background.paper,
                          borderRadius: 4,
                          color: theme.palette.text.primary,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                        labelStyle={{ color: theme.palette.text.primary }}
                      />
                      <Bar
                        dataKey="count"
                        fill="#8884d8"
                        name={t("common:count")}
                        activeBar={false}
                        onMouseEnter={(_, index) =>
                          setActiveIndices((prev) => ({
                            ...prev,
                            [column]: index,
                          }))
                        }
                        onMouseLeave={() =>
                          setActiveIndices((prev) => ({
                            ...prev,
                            [column]: null,
                          }))
                        }
                      >
                        {stats.top_5.map((_, index) => {
                          const activeIndex = activeIndices[column] ?? null;
                          return (
                            <Cell
                              key={index}
                              fill="#8884d8"
                              fillOpacity={
                                index === activeIndex
                                  ? 1
                                  : activeIndex !== null
                                    ? 0.5
                                    : 0.7
                              }
                            />
                          );
                        })}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </Box>

              {/* Proportion */}
              <Box flex="1 1 400px" minWidth="300px">
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                >
                  {t("datasets:label.proportion")}
                </Typography>
                <Box sx={{ width: "100%", height: 250 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={stats.top_5}
                        dataKey="count"
                        nameKey="value"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label
                      >
                        {stats.top_5.map((entry, index) => (
                          <Cell
                            key={index}
                            fill={
                              (theme.palette.chart.palette ?? [
                                theme.palette.chart.train,
                                theme.palette.chart.test,
                                theme.palette.chart.validation,
                                theme.palette.secondary.main,
                                theme.palette.primary.main,
                              ])[index]
                            }
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: theme.palette.background.paper,
                          borderRadius: 4,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                        labelStyle={{ color: theme.palette.text.primary }}
                        itemStyle={{ color: theme.palette.text.primary }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </Box>
            </Box>
          </CardContent>
        </ExportableCard>
      ))}
      {remaining > 0 && (
        <Box display="flex" justifyContent="center" mt={1} mb={2}>
          <Button
            variant="outlined"
            onClick={() => setVisibleCount((c) => c + BATCH_SIZE)}
          >
            {t("datasets:label.showMore", { count: remaining })}
          </Button>
        </Box>
      )}
    </Box>
  );
};
