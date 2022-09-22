import csv
import os
import shutil

FIELDNAMES = ["asset", "platform", "alert_id", "severity", "name", "description"]

if __name__ == "__main__":
  print("Compiling dataset...")

  files = []

  for folder in os.listdir("cache/snapshots"):
    for file in os.listdir(f"cache/snapshots/{folder}"):
      if file.endswith(".csv"):
        files.append(f"cache/snapshots/{folder}/{file}")

  if len(files) == 0:
    exit()

  rows = []

  if os.path.exists("dataset.csv"):
    with open("dataset.csv", "r", newline="") as dataset:
      reader = csv.DictReader(dataset)
      for row in reader:
        rows.append(row)

  for path in files:
    with open(path, "r", newline="") as file:
      reader = csv.DictReader(file)
      for row in reader:
        rows.append(row)

  # Remove duplicates
  rows = [dict(item) for item in set(frozenset(row.items()) for row in rows)]

  with open("dataset.csv", "w", newline="") as dataset:
    writer = csv.DictWriter(dataset, fieldnames=FIELDNAMES, escapechar="\\")
    writer.writeheader()
    writer.writerows(rows)

  print(f"Compiled dataset.csv")

  shutil.rmtree("cache/snapshots")
