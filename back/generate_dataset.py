import csv
import json

csvFilePath = "Example_dataset/Twitter_Data.csv"
jsonFilePath = "Example_dataset/twitterDataset.json"

size = 1000

data = {"train": {"x": [], "y": []}, "test": {"x": [], "y": []}}

with open(csvFilePath, encoding="utf8") as csvFile:
    csvReader = csv.DictReader(csvFile)
    c = 0
    p = 0
    for row in csvReader:
        try:
            actual_data = [row["clean_text"], int(row["category"])]
        except Exception as e:
            print(e)
            continue

        if actual_data[1] == 0:
            continue

        if c == size:
            c = 0
            p += 1
        if p == 0:
            data["train"]["x"].append(actual_data[0])
            data["train"]["y"].append(actual_data[1])
        elif p == 1:
            data["test"]["x"].append(actual_data[0])
            data["test"]["y"].append(actual_data[1])
        else:
            break
        c += 1

with open(jsonFilePath, "w") as jsonFile:
    jsonFile.write(json.dumps(data, indent=4))
