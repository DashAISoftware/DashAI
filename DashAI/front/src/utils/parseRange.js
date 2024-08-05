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

export function parseIndexToRange(indexArray) {
  if (indexArray.length === 0) {
    return "";
  }
  const ranges = [];
  let min = indexArray[0];
  let max = indexArray[0];
  for (let i = 1; i < indexArray.length; i++) {
    if (indexArray[i] === max + 1) {
      max = indexArray[i];
    } else {
      if (min === max) {
        ranges.push(min.toString());
      } else {
        ranges.push(`${min}-${max}`);
      }
      min = indexArray[i];
      max = indexArray[i];
    }
  }
  if (min === max) {
    ranges.push(min.toString());
  } else {
    ranges.push(`${min}-${max}`);
  }
  return ranges.join(",");
}
