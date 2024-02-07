import React from "react";
import PluginsToolbar from "./PluginsToolbar";
import PropTypes from "prop-types";
import PluginsGrid from "./PluginsGrid";

function PluginsContent({ Plugins }) {
  const [pluginsToShow, setPluginsToShow] = React.useState(Plugins);
  const [cardView, setCardView] = React.useState(true);
  const [searchField, setSearchField] = React.useState("");
  const [type, setType] = React.useState("");
  const [sortBy, setSortBy] = React.useState("latest");

  const handleCardViewChange = (event, nextView) => {
    setCardView(nextView);
  };

  const handleSearchFieldChange = (event) => {
    setSearchField(event.target.value);
  };

  const handleTypeChange = (event) => {
    setType(event.target.value);
  };

  const handleSortByChange = (event) => {
    setSortBy(event.target.value);
  };

  function filterPlugins(searchValue, typeValue) {
    const filteredPlugins = Plugins.filter((plugin) => {
      const includesSearch = plugin.name.toLowerCase().includes(searchValue);
      const includesType = typeValue === "" || plugin.tags.includes(typeValue);
      return includesSearch && includesType;
    });
    setPluginsToShow(filteredPlugins);
  }

  React.useEffect(() => {
    filterPlugins(searchField, type);
  }, [searchField, type]);

  return (
    <>
      <PluginsToolbar
        cardView={cardView}
        handleCardViewChange={handleCardViewChange}
        searchField={searchField}
        handleSearchFieldChange={handleSearchFieldChange}
        type={type}
        handleTypeChange={handleTypeChange}
        sortBy={sortBy}
        handleSortByChange={handleSortByChange}
      />
      <PluginsGrid pluginsToShow={pluginsToShow} cardView={cardView} />
    </>
  );
}

PluginsContent.propTypes = {
  Plugins: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      tags: PropTypes.arrayOf(PropTypes.string).isRequired,
      installed: PropTypes.bool,
      enabled: PropTypes.bool,
    }),
  ),
};

export default PluginsContent;
