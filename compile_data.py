import os
import shutil
import pandas as pd

FIELDNAMES = ["asset", "platform", "alert_id", "severity", "name", "description"]

if __name__ == "__main__":
  files = []

  if os.path.exists("dataset.csv"):
    files.append("dataset.csv")

  if os.path.exists("cache/snapshots"):
    for folder in os.listdir("cache/snapshots"):
      for file in os.listdir(f"cache/snapshots/{folder}"):
        if file.endswith(".csv"):
          files.append(f"cache/snapshots/{folder}/{file}")

  if len(files) == 0 or files == ["dataset.csv"]:
    print("Nothing to compile")
    exit()

  print("Compiling dataset...")

  df = pd.DataFrame([], columns=FIELDNAMES)

  for path in files:
    df = pd.concat([df, pd.read_csv(path)])

  df = df.drop_duplicates()
  df = df.sort_values("asset")
  df.to_csv("dataset.csv", index=False, escapechar="\\")

  print("Compiled dataset.csv")

  shutil.rmtree("cache/snapshots")
