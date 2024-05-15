import { useEffect, useState } from "react";

/**
 * Custom hook to display plugins and control toolbar
 * @param {object} plugins plugins to display
 * @returns pluginsToShow, hooks for toolbar
 */
export default function usePluginsContent({ plugins }) {
  const [pluginsToShow, setPluginsToShow] = useState(plugins);

  const [searchField, setSearchField] = useState("");
  const [type, setType] = useState("");
  const [sortBy, setSortBy] = useState("latest");

  const handleSearchFieldChange = (event) => {
    setSearchField(event.target.value);
  };

  const handleTypeChange = (event) => {
    setType(event.target.value);
  };

  const handleSortByChange = (event) => {
    setSortBy(event.target.value);
  };

  function filterPlugins() {
    const filteredPlugins = plugins.filter((plugin) => {
      const includesSearch = plugin.name
        .toLowerCase()
        .replace(/-/g, " ")
        .includes(searchField.toLowerCase().replace(/-/g, " "));
      const includesType =
        type === "" || plugin.tags.some((tag) => tag.name === type);
      return includesSearch && includesType;
    });
    switch (sortBy) {
      case "latest": {
        filteredPlugins.sort(
          (a, b) => new Date(b.created) - new Date(a.created),
        );
        break;
      }
      default: {
        filteredPlugins.sort(
          (a, b) => new Date(a.created) - new Date(b.created),
        );
      }
    }
    setPluginsToShow(filteredPlugins);
  }

  useEffect(() => {
    filterPlugins();
  }, [searchField, type, sortBy]);

  return {
    pluginsToShow,
    searchField,
    handleSearchFieldChange,
    type,
    handleTypeChange,
    sortBy,
    handleSortByChange,
  };
}
