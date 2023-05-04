export const formatDate = (date) => {
  if (date == null) {
    return "";
  }
  return new Date(date).toLocaleDateString();
};
