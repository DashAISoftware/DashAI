import csv
import json

csvFilePath1 = "example_dataset/twitter_training.csv"
csvFilePath2 = "example_dataset/twitter_validation.csv"
jsonFilePath = "example_dataset/twitterDataset.json"

size = 1000

data = {
    "task_info":{
        "task_type":"TextClassificationTask"
    },
    "train": {"x": [], "y": []}, 
    "test": {"x": [], "y": []}}

i = 0
with open(csvFilePath1, encoding="utf8") as csvFile:
    csvReader = csv.DictReader(csvFile)
    keys = []
    for row in csvReader:
        keys = list(row.keys())
        data["train"]["x"].append(row[keys[3]])
        data["train"]["y"].append(row[keys[2]])

        i += 1
        if i > 5000:
            break

i = 0
with open(csvFilePath2, encoding="utf8") as csvFile:
    csvReader = csv.DictReader(csvFile)
    keys = []
    for row in csvReader:
        keys = list(row.keys())
        data["test"]["x"].append(row[keys[3]])
        data["test"]["y"].append(row[keys[2]])
        
        i += 1
        if i > 5000:
            break

with open(jsonFilePath, "w") as jsonFile:
    jsonFile.write(json.dumps(data, indent=4))

# with open(csvFilePath, encoding="utf8") as csvFile:
#     csvReader = csv.DictReader(csvFile)
#     c = 0
#     p = 0
#     for row in csvReader:
#         try:
#             actual_data = [row["clean_text"], int(row["category"])]
#         except Exception as e:
#             print(e)
#             continue

#         if actual_data[1] == 0:
#             continue

#         if c == size:
#             c = 0
#             p += 1
#         if p == 0:
#             data["train"]["x"].append(actual_data[0])
#             data["train"]["y"].append(actual_data[1])
#         elif p == 1:
#             data["test"]["x"].append(actual_data[0])
#             data["test"]["y"].append(actual_data[1])
#         else:
#             break
#         c += 1


