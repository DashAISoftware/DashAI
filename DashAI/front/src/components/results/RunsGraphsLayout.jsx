// Add news graphs and how to generate if applies
function layoutMaking (selectedChart, graphsToView) {

    let pieValuesLength = graphsToView.pie.length

    // General Layout
    const generalLayout = {
        polar: { radialaxis: { visible: selectedChart === "radar", range: [0, 1] } },
        showlegend: true,
        width: 600,
        height: 400,
    };

    // Layout only for Pie Charts
    let numRows, numColumns;
      if (pieValuesLength <= 2) {
        numRows = 1;
        numColumns = pieValuesLength;
      } else {
        numRows = Math.ceil(pieValuesLength / 2);
        numColumns = Math.min(2, pieValuesLength);
      }

    const pieLayout = {
        height: 400,
        width: 600,
        grid: {rows: numRows, columns: numColumns},
        legend: {
          itemclick: false
        }
      };

    return {generalLayout,pieLayout};
  }

export default layoutMaking;