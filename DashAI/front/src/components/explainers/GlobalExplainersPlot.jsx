import React from "react";
import { Grid } from "@mui/material";
import Plot from "react-plotly.js";
import PropTypes from "prop-types";

const pfi = {
  data: [
    {
      alignmentgroup: "True",
      error_x: { array: [0.08, 0.098, 0.233] },
      hovertemplate:
        "x=%{x}\u003cbr\u003ey=%{y}\u003cextra\u003e\u003c\u002fextra\u003e",
      legendgroup: "",
      marker: { color: "#636efa", pattern: { shape: "" } },
      name: "",
      offsetgroup: "",
      orientation: "h",
      showlegend: false,
      textposition: "auto",
      x: [0.007, 0.047, 0.527],
      xaxis: "x",
      y: ["SepalWidthCm", "SepalLengthCm", "PetalWidthCm"],
      yaxis: "y",
      type: "bar",
    },
  ],
  layout: {
    template: {
      data: {
        histogram2dcontour: [
          {
            type: "histogram2dcontour",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        choropleth: [
          { type: "choropleth", colorbar: { outlinewidth: 0, ticks: "" } },
        ],
        histogram2d: [
          {
            type: "histogram2d",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        heatmap: [
          {
            type: "heatmap",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        heatmapgl: [
          {
            type: "heatmapgl",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        contourcarpet: [
          { type: "contourcarpet", colorbar: { outlinewidth: 0, ticks: "" } },
        ],
        contour: [
          {
            type: "contour",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        surface: [
          {
            type: "surface",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        mesh3d: [{ type: "mesh3d", colorbar: { outlinewidth: 0, ticks: "" } }],
        scatter: [
          {
            fillpattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            type: "scatter",
          },
        ],
        parcoords: [
          {
            type: "parcoords",
            line: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatterpolargl: [
          {
            type: "scatterpolargl",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        bar: [
          {
            error_x: { color: "#2a3f5f" },
            error_y: { color: "#2a3f5f" },
            marker: {
              line: { color: "#E5ECF6", width: 0.5 },
              pattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            },
            type: "bar",
          },
        ],
        scattergeo: [
          {
            type: "scattergeo",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatterpolar: [
          {
            type: "scatterpolar",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        histogram: [
          {
            marker: {
              pattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            },
            type: "histogram",
          },
        ],
        scattergl: [
          {
            type: "scattergl",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatter3d: [
          {
            type: "scatter3d",
            line: { colorbar: { outlinewidth: 0, ticks: "" } },
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scattermapbox: [
          {
            type: "scattermapbox",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatterternary: [
          {
            type: "scatterternary",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scattercarpet: [
          {
            type: "scattercarpet",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        carpet: [
          {
            aaxis: {
              endlinecolor: "#2a3f5f",
              gridcolor: "white",
              linecolor: "white",
              minorgridcolor: "white",
              startlinecolor: "#2a3f5f",
            },
            baxis: {
              endlinecolor: "#2a3f5f",
              gridcolor: "white",
              linecolor: "white",
              minorgridcolor: "white",
              startlinecolor: "#2a3f5f",
            },
            type: "carpet",
          },
        ],
        table: [
          {
            cells: { fill: { color: "#EBF0F8" }, line: { color: "white" } },
            header: { fill: { color: "#C8D4E3" }, line: { color: "white" } },
            type: "table",
          },
        ],
        barpolar: [
          {
            marker: {
              line: { color: "#E5ECF6", width: 0.5 },
              pattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            },
            type: "barpolar",
          },
        ],
        pie: [{ automargin: true, type: "pie" }],
      },
      layout: {
        autotypenumbers: "strict",
        colorway: [
          "#636efa",
          "#EF553B",
          "#00cc96",
          "#ab63fa",
          "#FFA15A",
          "#19d3f3",
          "#FF6692",
          "#B6E880",
          "#FF97FF",
          "#FECB52",
        ],
        font: { color: "#2a3f5f" },
        hovermode: "closest",
        hoverlabel: { align: "left" },
        paper_bgcolor: "white",
        plot_bgcolor: "#E5ECF6",
        polar: {
          bgcolor: "#E5ECF6",
          angularaxis: { gridcolor: "white", linecolor: "white", ticks: "" },
          radialaxis: { gridcolor: "white", linecolor: "white", ticks: "" },
        },
        ternary: {
          bgcolor: "#E5ECF6",
          aaxis: { gridcolor: "white", linecolor: "white", ticks: "" },
          baxis: { gridcolor: "white", linecolor: "white", ticks: "" },
          caxis: { gridcolor: "white", linecolor: "white", ticks: "" },
        },
        coloraxis: { colorbar: { outlinewidth: 0, ticks: "" } },
        colorscale: {
          sequential: [
            [0.0, "#0d0887"],
            [0.1111111111111111, "#46039f"],
            [0.2222222222222222, "#7201a8"],
            [0.3333333333333333, "#9c179e"],
            [0.4444444444444444, "#bd3786"],
            [0.5555555555555556, "#d8576b"],
            [0.6666666666666666, "#ed7953"],
            [0.7777777777777778, "#fb9f3a"],
            [0.8888888888888888, "#fdca26"],
            [1.0, "#f0f921"],
          ],
          sequentialminus: [
            [0.0, "#0d0887"],
            [0.1111111111111111, "#46039f"],
            [0.2222222222222222, "#7201a8"],
            [0.3333333333333333, "#9c179e"],
            [0.4444444444444444, "#bd3786"],
            [0.5555555555555556, "#d8576b"],
            [0.6666666666666666, "#ed7953"],
            [0.7777777777777778, "#fb9f3a"],
            [0.8888888888888888, "#fdca26"],
            [1.0, "#f0f921"],
          ],
          diverging: [
            [0, "#8e0152"],
            [0.1, "#c51b7d"],
            [0.2, "#de77ae"],
            [0.3, "#f1b6da"],
            [0.4, "#fde0ef"],
            [0.5, "#f7f7f7"],
            [0.6, "#e6f5d0"],
            [0.7, "#b8e186"],
            [0.8, "#7fbc41"],
            [0.9, "#4d9221"],
            [1, "#276419"],
          ],
        },
        xaxis: {
          gridcolor: "white",
          linecolor: "white",
          ticks: "",
          title: { standoff: 15 },
          zerolinecolor: "white",
          automargin: true,
          zerolinewidth: 2,
        },
        yaxis: {
          gridcolor: "white",
          linecolor: "white",
          ticks: "",
          title: { standoff: 15 },
          zerolinecolor: "white",
          automargin: true,
          zerolinewidth: 2,
        },
        scene: {
          xaxis: {
            backgroundcolor: "#E5ECF6",
            gridcolor: "white",
            linecolor: "white",
            showbackground: true,
            ticks: "",
            zerolinecolor: "white",
            gridwidth: 2,
          },
          yaxis: {
            backgroundcolor: "#E5ECF6",
            gridcolor: "white",
            linecolor: "white",
            showbackground: true,
            ticks: "",
            zerolinecolor: "white",
            gridwidth: 2,
          },
          zaxis: {
            backgroundcolor: "#E5ECF6",
            gridcolor: "white",
            linecolor: "white",
            showbackground: true,
            ticks: "",
            zerolinecolor: "white",
            gridwidth: 2,
          },
        },
        shapedefaults: { line: { color: "#2a3f5f" } },
        annotationdefaults: {
          arrowcolor: "#2a3f5f",
          arrowhead: 0,
          arrowwidth: 1,
        },
        geo: {
          bgcolor: "white",
          landcolor: "#E5ECF6",
          subunitcolor: "white",
          showland: true,
          showlakes: true,
          lakecolor: "white",
        },
        title: { x: 0.05 },
        mapbox: { style: "light" },
      },
    },
    xaxis: { anchor: "y", domain: [0.0, 1.0], title: { text: "Importance" } },
    yaxis: { anchor: "x", domain: [0.0, 1.0], title: {} },
    legend: { tracegroupgap: 0 },
    margin: { t: 60 },
    barmode: "relative",
    annotations: [
      {
        showarrow: false,
        text: "Number of features: ",
        x: 0,
        xanchor: "left",
        y: 1.15,
        yanchor: "top",
        yref: "paper",
      },
    ],
    updatemenus: [
      {
        buttons: [
          {
            args: [{ x: [[0.527]], y: [["PetalWidthCm"]] }],
            label: "1",
            method: "restyle",
          },
          {
            args: [
              { x: [[0.047, 0.527]], y: [["SepalLengthCm", "PetalWidthCm"]] },
            ],
            label: "2",
            method: "restyle",
          },
          {
            args: [
              {
                x: [[0.007, 0.047, 0.527]],
                y: [["SepalWidthCm", "SepalLengthCm", "PetalWidthCm"]],
              },
            ],
            label: "3",
            method: "restyle",
          },
        ],
        x: 0.25,
        xanchor: "left",
        y: 1.2,
        yanchor: "top",
      },
    ],
  },
};
const pdp = {
  data: [
    {
      hovertemplate:
        "Feature value=%{x}\u003cbr\u003ey=%{y}\u003cextra\u003e\u003c\u002fextra\u003e",
      legendgroup: "",
      line: { color: "#636efa", dash: "solid" },
      marker: { symbol: "circle" },
      mode: "lines",
      name: "",
      orientation: "v",
      showlegend: false,
      x: [
        4.4, 4.8, 4.9, 5.0, 5.1, 5.2, 5.4, 5.5, 5.6, 5.7, 5.8, 6.0, 6.1, 6.2,
        6.3, 6.4, 6.5, 6.7, 6.8, 6.9, 7.3,
      ],
      xaxis: "x",
      y: [
        0.283, 0.293, 0.302, 0.373, 0.414, 0.393, 0.414, 0.514, 0.53, 0.521,
        0.464, 0.425, 0.43, 0.427, 0.389, 0.407, 0.403, 0.414, 0.401, 0.389,
        0.249,
      ],
      yaxis: "y",
      type: "scatter",
    },
  ],
  layout: {
    template: {
      data: {
        histogram2dcontour: [
          {
            type: "histogram2dcontour",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        choropleth: [
          { type: "choropleth", colorbar: { outlinewidth: 0, ticks: "" } },
        ],
        histogram2d: [
          {
            type: "histogram2d",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        heatmap: [
          {
            type: "heatmap",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        heatmapgl: [
          {
            type: "heatmapgl",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        contourcarpet: [
          { type: "contourcarpet", colorbar: { outlinewidth: 0, ticks: "" } },
        ],
        contour: [
          {
            type: "contour",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        surface: [
          {
            type: "surface",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        mesh3d: [{ type: "mesh3d", colorbar: { outlinewidth: 0, ticks: "" } }],
        scatter: [
          {
            fillpattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            type: "scatter",
          },
        ],
        parcoords: [
          {
            type: "parcoords",
            line: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatterpolargl: [
          {
            type: "scatterpolargl",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        bar: [
          {
            error_x: { color: "#2a3f5f" },
            error_y: { color: "#2a3f5f" },
            marker: {
              line: { color: "#E5ECF6", width: 0.5 },
              pattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            },
            type: "bar",
          },
        ],
        scattergeo: [
          {
            type: "scattergeo",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatterpolar: [
          {
            type: "scatterpolar",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        histogram: [
          {
            marker: {
              pattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            },
            type: "histogram",
          },
        ],
        scattergl: [
          {
            type: "scattergl",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatter3d: [
          {
            type: "scatter3d",
            line: { colorbar: { outlinewidth: 0, ticks: "" } },
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scattermapbox: [
          {
            type: "scattermapbox",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatterternary: [
          {
            type: "scatterternary",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scattercarpet: [
          {
            type: "scattercarpet",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        carpet: [
          {
            aaxis: {
              endlinecolor: "#2a3f5f",
              gridcolor: "white",
              linecolor: "white",
              minorgridcolor: "white",
              startlinecolor: "#2a3f5f",
            },
            baxis: {
              endlinecolor: "#2a3f5f",
              gridcolor: "white",
              linecolor: "white",
              minorgridcolor: "white",
              startlinecolor: "#2a3f5f",
            },
            type: "carpet",
          },
        ],
        table: [
          {
            cells: { fill: { color: "#EBF0F8" }, line: { color: "white" } },
            header: { fill: { color: "#C8D4E3" }, line: { color: "white" } },
            type: "table",
          },
        ],
        barpolar: [
          {
            marker: {
              line: { color: "#E5ECF6", width: 0.5 },
              pattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            },
            type: "barpolar",
          },
        ],
        pie: [{ automargin: true, type: "pie" }],
      },
      layout: {
        autotypenumbers: "strict",
        colorway: [
          "#636efa",
          "#EF553B",
          "#00cc96",
          "#ab63fa",
          "#FFA15A",
          "#19d3f3",
          "#FF6692",
          "#B6E880",
          "#FF97FF",
          "#FECB52",
        ],
        font: { color: "#2a3f5f" },
        hovermode: "closest",
        hoverlabel: { align: "left" },
        paper_bgcolor: "white",
        plot_bgcolor: "#E5ECF6",
        polar: {
          bgcolor: "#E5ECF6",
          angularaxis: { gridcolor: "white", linecolor: "white", ticks: "" },
          radialaxis: { gridcolor: "white", linecolor: "white", ticks: "" },
        },
        ternary: {
          bgcolor: "#E5ECF6",
          aaxis: { gridcolor: "white", linecolor: "white", ticks: "" },
          baxis: { gridcolor: "white", linecolor: "white", ticks: "" },
          caxis: { gridcolor: "white", linecolor: "white", ticks: "" },
        },
        coloraxis: { colorbar: { outlinewidth: 0, ticks: "" } },
        colorscale: {
          sequential: [
            [0.0, "#0d0887"],
            [0.1111111111111111, "#46039f"],
            [0.2222222222222222, "#7201a8"],
            [0.3333333333333333, "#9c179e"],
            [0.4444444444444444, "#bd3786"],
            [0.5555555555555556, "#d8576b"],
            [0.6666666666666666, "#ed7953"],
            [0.7777777777777778, "#fb9f3a"],
            [0.8888888888888888, "#fdca26"],
            [1.0, "#f0f921"],
          ],
          sequentialminus: [
            [0.0, "#0d0887"],
            [0.1111111111111111, "#46039f"],
            [0.2222222222222222, "#7201a8"],
            [0.3333333333333333, "#9c179e"],
            [0.4444444444444444, "#bd3786"],
            [0.5555555555555556, "#d8576b"],
            [0.6666666666666666, "#ed7953"],
            [0.7777777777777778, "#fb9f3a"],
            [0.8888888888888888, "#fdca26"],
            [1.0, "#f0f921"],
          ],
          diverging: [
            [0, "#8e0152"],
            [0.1, "#c51b7d"],
            [0.2, "#de77ae"],
            [0.3, "#f1b6da"],
            [0.4, "#fde0ef"],
            [0.5, "#f7f7f7"],
            [0.6, "#e6f5d0"],
            [0.7, "#b8e186"],
            [0.8, "#7fbc41"],
            [0.9, "#4d9221"],
            [1, "#276419"],
          ],
        },
        xaxis: {
          gridcolor: "white",
          linecolor: "white",
          ticks: "",
          title: { standoff: 15 },
          zerolinecolor: "white",
          automargin: true,
          zerolinewidth: 2,
        },
        yaxis: {
          gridcolor: "white",
          linecolor: "white",
          ticks: "",
          title: { standoff: 15 },
          zerolinecolor: "white",
          automargin: true,
          zerolinewidth: 2,
        },
        scene: {
          xaxis: {
            backgroundcolor: "#E5ECF6",
            gridcolor: "white",
            linecolor: "white",
            showbackground: true,
            ticks: "",
            zerolinecolor: "white",
            gridwidth: 2,
          },
          yaxis: {
            backgroundcolor: "#E5ECF6",
            gridcolor: "white",
            linecolor: "white",
            showbackground: true,
            ticks: "",
            zerolinecolor: "white",
            gridwidth: 2,
          },
          zaxis: {
            backgroundcolor: "#E5ECF6",
            gridcolor: "white",
            linecolor: "white",
            showbackground: true,
            ticks: "",
            zerolinecolor: "white",
            gridwidth: 2,
          },
        },
        shapedefaults: { line: { color: "#2a3f5f" } },
        annotationdefaults: {
          arrowcolor: "#2a3f5f",
          arrowhead: 0,
          arrowwidth: 1,
        },
        geo: {
          bgcolor: "white",
          landcolor: "#E5ECF6",
          subunitcolor: "white",
          showland: true,
          showlakes: true,
          lakecolor: "white",
        },
        title: { x: 0.05 },
        mapbox: { style: "light" },
      },
    },
    xaxis: {
      anchor: "y",
      domain: [0.0, 1.0],
      title: { text: "Feature value" },
    },
    yaxis: {
      anchor: "x",
      domain: [0.0, 1.0],
      title: { text: "Partial Dependence" },
    },
    legend: { tracegroupgap: 0 },
    margin: { t: 60 },
    updatemenus: [
      {
        buttons: [
          {
            args: [
              {
                x: [
                  [
                    4.4, 4.8, 4.9, 5.0, 5.1, 5.2, 5.4, 5.5, 5.6, 5.7, 5.8, 6.0,
                    6.1, 6.2, 6.3, 6.4, 6.5, 6.7, 6.8, 6.9, 7.3,
                  ],
                ],
                y: [
                  [
                    0.283, 0.293, 0.302, 0.373, 0.414, 0.393, 0.414, 0.514,
                    0.53, 0.521, 0.464, 0.425, 0.43, 0.427, 0.389, 0.407, 0.403,
                    0.414, 0.401, 0.389, 0.249,
                  ],
                ],
              },
            ],
            label: "class: Iris-versicolor, feature: SepalLengthCm",
            method: "restyle",
          },
          {
            args: [
              {
                x: [
                  [
                    4.4, 4.8, 4.9, 5.0, 5.1, 5.2, 5.4, 5.5, 5.6, 5.7, 5.8, 6.0,
                    6.1, 6.2, 6.3, 6.4, 6.5, 6.7, 6.8, 6.9, 7.3,
                  ],
                ],
                y: [
                  [
                    0.221, 0.226, 0.24, 0.171, 0.153, 0.153, 0.153, 0.179,
                    0.202, 0.212, 0.283, 0.353, 0.352, 0.362, 0.407, 0.397,
                    0.401, 0.392, 0.411, 0.422, 0.58,
                  ],
                ],
              },
            ],
            label: "class: Iris-virginica, feature: SepalLengthCm",
            method: "restyle",
          },
          {
            args: [
              {
                x: [
                  [
                    4.4, 4.8, 4.9, 5.0, 5.1, 5.2, 5.4, 5.5, 5.6, 5.7, 5.8, 6.0,
                    6.1, 6.2, 6.3, 6.4, 6.5, 6.7, 6.8, 6.9, 7.3,
                  ],
                ],
                y: [
                  [
                    0.496, 0.481, 0.458, 0.456, 0.433, 0.454, 0.433, 0.307,
                    0.268, 0.267, 0.252, 0.222, 0.219, 0.211, 0.204, 0.196,
                    0.196, 0.194, 0.189, 0.189, 0.17,
                  ],
                ],
              },
            ],
            label: "class: Iris-setosa, feature: SepalLengthCm",
            method: "restyle",
          },
          {
            args: [
              {
                x: [
                  [
                    2.2, 2.6, 2.7, 2.8, 2.9, 3.0, 3.1, 3.3, 3.4, 3.5, 3.7, 3.8,
                    3.9,
                  ],
                ],
                y: [
                  [
                    0.422, 0.456, 0.421, 0.389, 0.434, 0.374, 0.391, 0.404,
                    0.349, 0.302, 0.278, 0.265, 0.245,
                  ],
                ],
              },
            ],
            label: "class: Iris-versicolor, feature: SepalWidthCm",
            method: "restyle",
          },
          {
            args: [
              {
                x: [
                  [
                    2.2, 2.6, 2.7, 2.8, 2.9, 3.0, 3.1, 3.3, 3.4, 3.5, 3.7, 3.8,
                    3.9,
                  ],
                ],
                y: [
                  [
                    0.353, 0.338, 0.373, 0.36, 0.315, 0.307, 0.278, 0.256,
                    0.291, 0.273, 0.306, 0.3, 0.271,
                  ],
                ],
              },
            ],
            label: "class: Iris-virginica, feature: SepalWidthCm",
            method: "restyle",
          },
          {
            args: [
              {
                x: [
                  [
                    2.2, 2.6, 2.7, 2.8, 2.9, 3.0, 3.1, 3.3, 3.4, 3.5, 3.7, 3.8,
                    3.9,
                  ],
                ],
                y: [
                  [
                    0.225, 0.206, 0.206, 0.251, 0.251, 0.32, 0.332, 0.34, 0.36,
                    0.425, 0.416, 0.435, 0.484,
                  ],
                ],
              },
            ],
            label: "class: Iris-setosa, feature: SepalWidthCm",
            method: "restyle",
          },
          {
            args: [
              {
                x: [
                  [
                    0.1, 0.2, 0.3, 0.4, 1.0, 1.2, 1.3, 1.4, 1.5, 1.8, 2.1, 2.2,
                    2.3, 2.4, 2.5,
                  ],
                ],
                y: [
                  [
                    0.314, 0.314, 0.314, 0.314, 0.754, 0.769, 0.769, 0.764,
                    0.582, 0.235, 0.162, 0.162, 0.162, 0.162, 0.162,
                  ],
                ],
              },
            ],
            label: "class: Iris-versicolor, feature: PetalWidthCm",
            method: "restyle",
          },
          {
            args: [
              {
                x: [
                  [
                    0.1, 0.2, 0.3, 0.4, 1.0, 1.2, 1.3, 1.4, 1.5, 1.8, 2.1, 2.2,
                    2.3, 2.4, 2.5,
                  ],
                ],
                y: [
                  [
                    0.062, 0.062, 0.062, 0.062, 0.114, 0.124, 0.125, 0.132,
                    0.314, 0.671, 0.743, 0.743, 0.743, 0.743, 0.743,
                  ],
                ],
              },
            ],
            label: "class: Iris-virginica, feature: PetalWidthCm",
            method: "restyle",
          },
          {
            args: [
              {
                x: [
                  [
                    0.1, 0.2, 0.3, 0.4, 1.0, 1.2, 1.3, 1.4, 1.5, 1.8, 2.1, 2.2,
                    2.3, 2.4, 2.5,
                  ],
                ],
                y: [
                  [
                    0.624, 0.624, 0.624, 0.624, 0.132, 0.107, 0.106, 0.105,
                    0.104, 0.094, 0.094, 0.094, 0.094, 0.094, 0.094,
                  ],
                ],
              },
            ],
            label: "class: Iris-setosa, feature: PetalWidthCm",
            method: "restyle",
          },
        ],
        x: 0.3,
        xanchor: "left",
        y: 1.2,
        yanchor: "top",
      },
    ],
  },
};
const shap = {
  data: [
    {
      base: 0.3,
      measure: ["relative", "relative", "relative"],
      name: "20",
      orientation: "h",
      text: [-0.06, 0.09, -0.16],
      textposition: "outside",
      x: [-0.06, 0.09, -0.16],
      y: ["PetalWidthCm=0.2", "SepalWidthCm=2.9", "SepalLengthCm=4.4"],
      type: "waterfall",
    },
  ],
  layout: {
    template: {
      data: {
        histogram2dcontour: [
          {
            type: "histogram2dcontour",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        choropleth: [
          { type: "choropleth", colorbar: { outlinewidth: 0, ticks: "" } },
        ],
        histogram2d: [
          {
            type: "histogram2d",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        heatmap: [
          {
            type: "heatmap",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        heatmapgl: [
          {
            type: "heatmapgl",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        contourcarpet: [
          { type: "contourcarpet", colorbar: { outlinewidth: 0, ticks: "" } },
        ],
        contour: [
          {
            type: "contour",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        surface: [
          {
            type: "surface",
            colorbar: { outlinewidth: 0, ticks: "" },
            colorscale: [
              [0.0, "#0d0887"],
              [0.1111111111111111, "#46039f"],
              [0.2222222222222222, "#7201a8"],
              [0.3333333333333333, "#9c179e"],
              [0.4444444444444444, "#bd3786"],
              [0.5555555555555556, "#d8576b"],
              [0.6666666666666666, "#ed7953"],
              [0.7777777777777778, "#fb9f3a"],
              [0.8888888888888888, "#fdca26"],
              [1.0, "#f0f921"],
            ],
          },
        ],
        mesh3d: [{ type: "mesh3d", colorbar: { outlinewidth: 0, ticks: "" } }],
        scatter: [
          {
            fillpattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            type: "scatter",
          },
        ],
        parcoords: [
          {
            type: "parcoords",
            line: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatterpolargl: [
          {
            type: "scatterpolargl",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        bar: [
          {
            error_x: { color: "#2a3f5f" },
            error_y: { color: "#2a3f5f" },
            marker: {
              line: { color: "#E5ECF6", width: 0.5 },
              pattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            },
            type: "bar",
          },
        ],
        scattergeo: [
          {
            type: "scattergeo",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatterpolar: [
          {
            type: "scatterpolar",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        histogram: [
          {
            marker: {
              pattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            },
            type: "histogram",
          },
        ],
        scattergl: [
          {
            type: "scattergl",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatter3d: [
          {
            type: "scatter3d",
            line: { colorbar: { outlinewidth: 0, ticks: "" } },
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scattermapbox: [
          {
            type: "scattermapbox",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scatterternary: [
          {
            type: "scatterternary",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        scattercarpet: [
          {
            type: "scattercarpet",
            marker: { colorbar: { outlinewidth: 0, ticks: "" } },
          },
        ],
        carpet: [
          {
            aaxis: {
              endlinecolor: "#2a3f5f",
              gridcolor: "white",
              linecolor: "white",
              minorgridcolor: "white",
              startlinecolor: "#2a3f5f",
            },
            baxis: {
              endlinecolor: "#2a3f5f",
              gridcolor: "white",
              linecolor: "white",
              minorgridcolor: "white",
              startlinecolor: "#2a3f5f",
            },
            type: "carpet",
          },
        ],
        table: [
          {
            cells: { fill: { color: "#EBF0F8" }, line: { color: "white" } },
            header: { fill: { color: "#C8D4E3" }, line: { color: "white" } },
            type: "table",
          },
        ],
        barpolar: [
          {
            marker: {
              line: { color: "#E5ECF6", width: 0.5 },
              pattern: { fillmode: "overlay", size: 10, solidity: 0.2 },
            },
            type: "barpolar",
          },
        ],
        pie: [{ automargin: true, type: "pie" }],
      },
      layout: {
        autotypenumbers: "strict",
        colorway: [
          "#636efa",
          "#EF553B",
          "#00cc96",
          "#ab63fa",
          "#FFA15A",
          "#19d3f3",
          "#FF6692",
          "#B6E880",
          "#FF97FF",
          "#FECB52",
        ],
        font: { color: "#2a3f5f" },
        hovermode: "closest",
        hoverlabel: { align: "left" },
        paper_bgcolor: "white",
        plot_bgcolor: "#E5ECF6",
        polar: {
          bgcolor: "#E5ECF6",
          angularaxis: { gridcolor: "white", linecolor: "white", ticks: "" },
          radialaxis: { gridcolor: "white", linecolor: "white", ticks: "" },
        },
        ternary: {
          bgcolor: "#E5ECF6",
          aaxis: { gridcolor: "white", linecolor: "white", ticks: "" },
          baxis: { gridcolor: "white", linecolor: "white", ticks: "" },
          caxis: { gridcolor: "white", linecolor: "white", ticks: "" },
        },
        coloraxis: { colorbar: { outlinewidth: 0, ticks: "" } },
        colorscale: {
          sequential: [
            [0.0, "#0d0887"],
            [0.1111111111111111, "#46039f"],
            [0.2222222222222222, "#7201a8"],
            [0.3333333333333333, "#9c179e"],
            [0.4444444444444444, "#bd3786"],
            [0.5555555555555556, "#d8576b"],
            [0.6666666666666666, "#ed7953"],
            [0.7777777777777778, "#fb9f3a"],
            [0.8888888888888888, "#fdca26"],
            [1.0, "#f0f921"],
          ],
          sequentialminus: [
            [0.0, "#0d0887"],
            [0.1111111111111111, "#46039f"],
            [0.2222222222222222, "#7201a8"],
            [0.3333333333333333, "#9c179e"],
            [0.4444444444444444, "#bd3786"],
            [0.5555555555555556, "#d8576b"],
            [0.6666666666666666, "#ed7953"],
            [0.7777777777777778, "#fb9f3a"],
            [0.8888888888888888, "#fdca26"],
            [1.0, "#f0f921"],
          ],
          diverging: [
            [0, "#8e0152"],
            [0.1, "#c51b7d"],
            [0.2, "#de77ae"],
            [0.3, "#f1b6da"],
            [0.4, "#fde0ef"],
            [0.5, "#f7f7f7"],
            [0.6, "#e6f5d0"],
            [0.7, "#b8e186"],
            [0.8, "#7fbc41"],
            [0.9, "#4d9221"],
            [1, "#276419"],
          ],
        },
        xaxis: {
          gridcolor: "white",
          linecolor: "white",
          ticks: "",
          title: { standoff: 15 },
          zerolinecolor: "white",
          automargin: true,
          zerolinewidth: 2,
        },
        yaxis: {
          gridcolor: "white",
          linecolor: "white",
          ticks: "",
          title: { standoff: 15 },
          zerolinecolor: "white",
          automargin: true,
          zerolinewidth: 2,
        },
        scene: {
          xaxis: {
            backgroundcolor: "#E5ECF6",
            gridcolor: "white",
            linecolor: "white",
            showbackground: true,
            ticks: "",
            zerolinecolor: "white",
            gridwidth: 2,
          },
          yaxis: {
            backgroundcolor: "#E5ECF6",
            gridcolor: "white",
            linecolor: "white",
            showbackground: true,
            ticks: "",
            zerolinecolor: "white",
            gridwidth: 2,
          },
          zaxis: {
            backgroundcolor: "#E5ECF6",
            gridcolor: "white",
            linecolor: "white",
            showbackground: true,
            ticks: "",
            zerolinecolor: "white",
            gridwidth: 2,
          },
        },
        shapedefaults: { line: { color: "#2a3f5f" } },
        annotationdefaults: {
          arrowcolor: "#2a3f5f",
          arrowhead: 0,
          arrowwidth: 1,
        },
        geo: {
          bgcolor: "white",
          landcolor: "#E5ECF6",
          subunitcolor: "white",
          showland: true,
          showlakes: true,
          lakecolor: "white",
        },
        title: { x: 0.05 },
        mapbox: { style: "light" },
      },
    },
    margin: { pad: 20, l: 100, r: 130, t: 60, b: 10 },
    xaxis: {
      title: { text: "Variables" },
      tickangle: 0,
      tickwidth: 100,
      showgrid: true,
      gridcolor: "#1B2631",
      gridwidth: 1,
      tickmode: "array",
      nticks: 2,
      tickvals: [0.3, 0.17],
      ticktext: ["E[f(x)]=0.3", "f(x)=0.17"],
    },
    yaxis: { showgrid: true, tickwidth: 150 },
    annotations: [
      {
        font: { size: 15 },
        showarrow: false,
        text: "The predicted value was: 1 with a probabiliy f(x)=0.17. The actual class is: {'Species': 1}",
        x: 0.2,
        xanchor: "left",
        xref: "paper",
        y: -0.35,
        yref: "paper",
      },
    ],
  },
};

/**
 * PartialDependencePlot function to generate data for the plot
 * @param {*} explanation explanation to plot
 * @returns data to plot, layout and actions modal
 */
function PartialDependencePlot(explanation) {
  const data = pdp.data;
  const layout = pdp.layout;

  function plotActions() {
    return (
      <Grid
        container
        display={"flex"}
        flexDirection={"column"}
        rowGap={2}
      ></Grid>
    );
  }
  return { data, layout, plotActions };
}

/**
 * PermutationFeatureImportancePlot function to generate data for the plot
 * @param {*} explanation explanation to plot
 * @returns data to plot, layout and actions modal
 */
function PermutationFeatureImportancePlot(explanation) {
  const data = pfi.data;
  const layout = pfi.layout;

  function plotActions() {
    return function plotActions() {
      return (
        <Grid
          container
          display={"flex"}
          flexDirection={"column"}
          rowGap={2}
        ></Grid>
      );
    };
  }
  return { data, layout, plotActions };
}

/**
 * KernelShapPlot function to generate data for the plot
 * @param {*} explanation explanation to plot
 * @returns data to plot, layout and actions modal
 */
function KernelShapPlot() {
  const data = shap.data;
  const layout = shap.layout;

  function plotActions() {
    return (
      <Grid container display={"flex"} flexDirection={"column"} rowGap={2}>
        <Grid item>
          <h5>ESTO ES SHAPPP</h5>
        </Grid>
      </Grid>
    );
  }
  return { data, layout, plotActions };
}

/**
 * GlobalExplainersPlot
 * @param {*} explainerType
 * @returns Component that renders the explanation plot and actions
 */
export default function GlobalExplainersPlot({ explainerType }) {
  // here explanations should be obtained from the back

  // explanation example for Partial Dependance
  const explanation1 = {
    battery_power: {
      grid_values: [
        504.0, 669.56, 835.11, 1000.67, 1166.22, 1331.78, 1497.33, 1662.89,
        1828.44, 1994.0,
      ],
      average: [
        [0.31, 0.31, 0.3, 0.29, 0.28, 0.23, 0.22, 0.21, 0.19, 0.18],
        [0.26, 0.25, 0.25, 0.25, 0.26, 0.27, 0.25, 0.25, 0.25, 0.26],
        [0.26, 0.26, 0.25, 0.25, 0.24, 0.23, 0.24, 0.25, 0.26, 0.26],
        [0.17, 0.18, 0.19, 0.2, 0.22, 0.27, 0.29, 0.29, 0.3, 0.3],
      ],
    },
    blue: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.24],
        [0.25, 0.25],
      ],
    },
    clock_speed: {
      grid_values: [0.5, 0.78, 1.06, 1.33, 1.61, 1.89, 2.17, 2.44, 2.72, 3.0],
      average: [
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26],
        [0.25, 0.26, 0.26, 0.26, 0.26, 0.26, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24],
      ],
    },
    dual_sim: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.26],
        [0.25, 0.25],
        [0.25, 0.25],
      ],
    },
    fc: {
      grid_values: [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0],
      average: [
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24],
        [0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26],
        [0.24, 0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26],
        [0.25, 0.25, 0.25, 0.24, 0.24, 0.24, 0.24, 0.24, 0.24, 0.24],
      ],
    },
    four_g: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.26],
        [0.25, 0.24],
        [0.25, 0.25],
      ],
    },
    int_memory: {
      grid_values: [
        2.0, 8.89, 15.78, 22.67, 29.56, 36.44, 43.33, 50.22, 57.11, 64.0,
      ],
      average: [
        [0.25, 0.26, 0.26, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.23],
        [0.26, 0.25, 0.25, 0.25, 0.26, 0.26, 0.25, 0.25, 0.25, 0.28],
        [0.27, 0.26, 0.25, 0.25, 0.24, 0.24, 0.24, 0.24, 0.24, 0.23],
        [0.23, 0.24, 0.24, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26, 0.26],
      ],
    },
    m_dep: {
      grid_values: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
      average: [
        [0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26, 0.27],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24],
      ],
    },
    mobile_wt: {
      grid_values: [
        80.0, 93.33, 106.67, 120.0, 133.33, 146.67, 160.0, 173.33, 186.67,
        200.0,
      ],
      average: [
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.26, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.22, 0.23, 0.24, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.25],
        [0.27, 0.27, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24, 0.23, 0.24],
      ],
    },
    n_cores: {
      grid_values: [1, 2, 3, 4, 5, 6, 7, 8],
      average: [
        [0.24, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26, 0.25],
        [0.29, 0.26, 0.26, 0.25, 0.24, 0.24, 0.24, 0.24],
        [0.22, 0.24, 0.24, 0.25, 0.25, 0.25, 0.25, 0.26],
        [0.25, 0.24, 0.24, 0.25, 0.25, 0.25, 0.25, 0.25],
      ],
    },
    pc: {
      grid_values: [
        0.0, 2.22, 4.44, 6.67, 8.89, 11.11, 13.33, 15.56, 17.78, 20.0,
      ],
      average: [
        [0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.27],
        [0.25, 0.25, 0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24],
        [0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24],
      ],
    },
    px_height: {
      grid_values: [
        13.0, 228.11, 443.22, 658.33, 873.44, 1088.56, 1303.67, 1518.78,
        1733.89, 1949.0,
      ],
      average: [
        [0.28, 0.27, 0.27, 0.25, 0.24, 0.23, 0.21, 0.19, 0.18, 0.17],
        [0.26, 0.25, 0.26, 0.26, 0.26, 0.26, 0.25, 0.25, 0.26, 0.25],
        [0.26, 0.25, 0.24, 0.24, 0.24, 0.24, 0.25, 0.25, 0.25, 0.28],
        [0.21, 0.23, 0.24, 0.25, 0.26, 0.28, 0.29, 0.3, 0.32, 0.3],
      ],
    },
    px_width: {
      grid_values: [
        503.0, 668.78, 834.56, 1000.33, 1166.11, 1331.89, 1497.67, 1663.44,
        1829.22, 1995.0,
      ],
      average: [
        [0.3, 0.27, 0.26, 0.26, 0.26, 0.26, 0.25, 0.23, 0.21, 0.2],
        [0.25, 0.26, 0.26, 0.26, 0.26, 0.25, 0.25, 0.24, 0.26, 0.27],
        [0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.23, 0.23],
        [0.21, 0.22, 0.22, 0.23, 0.23, 0.25, 0.25, 0.28, 0.3, 0.3],
      ],
    },
    ram: {
      grid_values: [
        258.0, 672.78, 1087.56, 1502.33, 1917.11, 2331.89, 2746.67, 3161.44,
        3576.22, 3991.0,
      ],
      average: [
        [0.73, 0.72, 0.57, 0.24, 0.12, 0.06, 0.04, 0.03, 0.03, 0.03],
        [0.18, 0.2, 0.32, 0.53, 0.53, 0.3, 0.14, 0.09, 0.08, 0.07],
        [0.06, 0.06, 0.08, 0.18, 0.28, 0.48, 0.53, 0.33, 0.23, 0.2],
        [0.03, 0.03, 0.03, 0.05, 0.07, 0.16, 0.29, 0.55, 0.67, 0.69],
      ],
    },
    sc_h: {
      grid_values: [
        5.0, 6.56, 8.11, 9.67, 11.22, 12.78, 14.33, 15.89, 17.44, 19.0,
      ],
      average: [
        [0.25, 0.25, 0.25, 0.26, 0.26, 0.26, 0.26, 0.25, 0.25, 0.26],
        [0.26, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24, 0.24, 0.25],
        [0.24, 0.24, 0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24],
      ],
    },
    sc_w: {
      grid_values: [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0],
      average: [
        [0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.25, 0.25, 0.24, 0.24],
        [0.25, 0.26, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24],
        [0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26],
        [0.25, 0.25, 0.25, 0.24, 0.24, 0.25, 0.25, 0.25, 0.26, 0.25],
      ],
    },
    talk_time: {
      grid_values: [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
      average: [
        [0.25, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.26, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.25, 0.26, 0.26],
        [0.25, 0.25, 0.25, 0.24, 0.24, 0.24, 0.25, 0.25, 0.25, 0.24],
        [0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
      ],
    },
    three_g: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.25],
      ],
    },
    touch_screen: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.25],
      ],
    },
    wifi: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.26],
        [0.25, 0.25],
        [0.25, 0.25],
      ],
    },
  };

  // explanation example for PermutationFeatureImportance
  const explanation4 = {
    features: [
      "ram",
      "wifi",
      "touch_screen",
      "three_g",
      "talk_time",
      "sc_w",
      "sc_h",
      "px_width",
      "px_height",
      "pc",
      "n_cores",
      "mobile_wt",
      "m_dep",
      "int_memory",
      "four_g",
      "fc",
      "dual_sim",
      "clock_speed",
      "blue",
      "battery_power",
    ],
    importances_mean: [
      0.56, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14,
      -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14,
    ],
  };

  /**
   * ExplainerRender function to switch between explainer types and call the right function to generate the plot data
   * @returns data to plot, layout and actions modal
   */
  function ExplainerRender() {
    switch (explainerType) {
      // should recieve a single generated explanation from the back, but for now uses the examples.
      case "PartialDependence":
        return PartialDependencePlot(explanation1);
      case "PermutationFeatureImportance":
        return PermutationFeatureImportancePlot(explanation4);
      case "KernelShap":
        return KernelShapPlot();
      default:
        return { data: [], plotActions: () => <></> };
    }
  }

  const { data, layout, plotActions } = ExplainerRender();

  return (
    <Grid item container flexDirection={"row"} justifyContent={"space-between"}>
      <Grid item xs={4}>
        {plotActions()}
      </Grid>
      <Grid item xs={8}>
        <Plot
          data={data}
          layout={{ ...layout, width: 480, height: 360 }}
          config={{ staticPlot: false }}
        />
      </Grid>
    </Grid>
  );
}

GlobalExplainersPlot.propTypes = {
  explainerType: PropTypes.string.isRequired,
};
