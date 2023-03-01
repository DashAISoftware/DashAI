import json

"""
    Convert old DashAI datasets in JSON format
    to the new format for JSON datasets.
"""
file_name = "dummy_text.json"
file = open(f"old_examples/{file_name}")
input_data = json.load(file)
file.close()

output_data = {"task_info": input_data["task_info"]["task_type"], "data": []}

for split in ["train", "test"]:
    n = len(input_data[split]["x"])
    for i in range(n):
        features = {}
        row = input_data[split]["x"][i]
        if type(row) == str:
            features["text"] = row
        else:
            for j in range(len(row)):
                features[f"feature_{j}"] = row[j]
        label = input_data[split]["y"][i]
        features["class"] = label
        output_data["data"].append(features)

with open(file_name, "w") as jsonFile:
    jsonFile.write(json.dumps(output_data, ensure_ascii=False, indent=4))
