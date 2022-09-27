import numpy as np
import pandas as pd


PLATFORMS = ["OpenSea", "LooksRare", "Foundation"]

SEVERITIES = ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]


def asset_alerts_data(df):
  data = df.value_counts("asset").to_dict().items()
  return pd.DataFrame(data, columns=["asset", "alerts"])

def alert_id_alerts_data(df):
  data = df.value_counts("alert_id").to_dict().items()
  return pd.DataFrame(data, columns=["alert_id", "alerts"])

def severity_alerts_data(df):
  counts = df.value_counts("severity")
  data = [[severity, counts[severity]] for severity in SEVERITIES]
  return pd.DataFrame(data, columns=["severity", "alerts"])

def asset_severity_alerts_data(df):
  data = df.value_counts(["asset", "severity"]).to_dict().items()
  data = map(lambda row: [*row[0], row[1]], data)
  return pd.DataFrame(data, columns=["asset", "severity", "alerts"])

def platform_alerts_assets_data(df):
  alert_counts = df.value_counts("platform")
  df = df.drop_duplicates(subset="asset")
  asset_counts = df.value_counts("platform")
  data = [[platform, alert_counts[platform], asset_counts[platform]] for platform in PLATFORMS]
  return pd.DataFrame(data, columns=["platform", "alerts", "assets"])

def platform_severity_percent_data(df):
  data = []

  for platform in PLATFORMS:
    row = [platform]
    p_df = df[df["platform"] == platform]
    severity_counts = p_df.value_counts("severity")
    severity_total = p_df.count()["severity"]

    for severity in SEVERITIES:
      if severity in severity_counts:
        row.append(severity_counts[severity] * 100 / severity_total)
      else:
        row.append(0)

    data.append(row)

  return pd.DataFrame(data, columns=["platform", *SEVERITIES])


if __name__ == "__main__":
  df = pd.read_csv("dataset.csv")

  print("----------------")
  print("Alerts per Asset")
  print("----------------")
  print(asset_alerts_data(df))

  print("-------------------")
  print("Alerts per Alert ID")
  print("-------------------")
  print(alert_id_alerts_data(df))

  print("-------------------")
  print("Alerts per Severity")
  print("-------------------")
  print(severity_alerts_data(df))

  print("-------------------------")
  print("Alerts per Asset Severity")
  print("-------------------------")
  print(asset_severity_alerts_data(df))

  print("--------------------------")
  print("Alerts/Assets per Platform")
  print("--------------------------")
  print(platform_alerts_assets_data(df))

  print("------------------------------")
  print("Platform Severity Distribution")
  print("------------------------------")
  print(platform_severity_percent_data(df))
