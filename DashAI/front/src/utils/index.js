export const formatDate = (date) => {
  if (date == null) {
    return "";
  }

  const formattedDate =
    // date.getDate() + "/" + (date.getMonth() + 1) + "/" + date.getFullYear();
    date;
  return formattedDate;
};
