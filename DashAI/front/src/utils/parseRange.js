const rangeRegex = /^(\d+)(-(\d+))*(,(\d+)(-(\d+))*)*$/;

export function parseRangeToIndex(range, maxValue) {
  const indexArray = [];
  if (!rangeRegex.test(range)) {
    throw new Error("The entered text doesn't fit the example format");
  }
  const ranges = range.split(",");
  ranges.forEach((range) => {
    const [min, max] = range.split("-");
    if (!range.includes("-") && parseInt(range) <= maxValue) {
      indexArray.push(parseInt(range));
    } else if (
      (!range.includes("-") && parseInt(range) > maxValue) ||
      parseInt(max) > maxValue
    ) {
      throw new Error(
        "The indexes should be minor than the total of columns or rows",
      );
    } else if (parseInt(min) > parseInt(max)) {
      throw new Error(
        "The second number of a range must be greater than the first",
      );
    } else {
      for (let i = parseInt(min); i <= parseInt(max); i++) {
        indexArray.push(i);
      }
    }
  });
  return indexArray;
}
