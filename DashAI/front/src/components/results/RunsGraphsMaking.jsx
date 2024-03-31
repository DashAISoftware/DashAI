// Add news graphs and how to generate if applies
function graphsMaking (graphsToView, item, relevantNumericValues, showCustomMetrics, selectedParameters, generalParameters, pieCounter) {

    graphsToView.radar = graphsToView.radar || [];
    graphsToView.bar = graphsToView.bar || [];
    graphsToView.pie = graphsToView.pie || [];

    // Radar Graph
    graphsToView.radar.push({
        type: "scatterpolar",
        name: item.name,
        automargin: true,
        r: relevantNumericValues,
        theta: showCustomMetrics ? selectedParameters : generalParameters,
        fill: "toself",
      });
      
    // Bar Graph
    graphsToView.bar.push({
        type: 'bar',
        automargin: true,
        name: item.name,
        x: showCustomMetrics ? selectedParameters : generalParameters,
        y: relevantNumericValues,
      });
    
    // Pie Graph
    graphsToView.pie.push({
        type: 'pie',
        name: item.name,
        automargin: true,
        title: item.name,
        labels: showCustomMetrics ? selectedParameters : generalParameters,
        values: relevantNumericValues,
        domain: {
          row: Math.floor(pieCounter / 2),
          column: pieCounter % 2
        },
        hoverinfo: 'label+percent+name',
        textinfo: 'percent',
        textposition: 'inside',
      });

      return graphsToView;
  }

export default graphsMaking;