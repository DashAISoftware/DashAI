// Add news graphs and how to generate if applies
function layoutMaking (selectedChart, graphsToView) {
    // General Layout
    const generalLayout = {
        polar: { radialaxis: { visible: selectedChart === "radar", range: [0, 1] } },
        showlegend: true,
        height: 480,
        width: 800,
    };

    // Layout only for Pie Charts
    let numRows, numColumns;
      if (graphsToView.pie.length <= 2) {
        numRows = 1;
        numColumns = graphsToView.pie.length;
      } else {
        numRows = Math.ceil(graphsToView.pie.length / 2);
        numColumns = Math.min(2, graphsToView.pie.length);
      }

    const pieLayout = {
        height: 480,
        width: 800,
        grid: {rows: numRows, columns: numColumns},
        legend: {
          itemclick: false
        }
      };

    return {generalLayout,pieLayout};
  }

export default layoutMaking;