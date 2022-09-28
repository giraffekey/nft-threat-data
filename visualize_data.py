from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import analyze_data


def plot_alert_id_alerts_data(df):
  df = analyze_data.alert_id_alerts_data(df)

  plt.figure(0)

  plt.barh(df["alert_id"], df["alerts"])
  plt.yticks(fontsize=6)
  plt.xlabel("Alert ID")
  plt.ylabel("Alerts")
  plt.title("Most Common Alerts")

def plot_severity_alerts_data(df):
  df = analyze_data.severity_alerts_data(df)

  plt.figure(1)

  plt.pie(df["alerts"], labels=df["severity"], colors=["green", "lime", "yellow", "orange", "red"])
  plt.title("Alerts per Severity")

def plot_asset_severity_alerts_data(df):
  df = analyze_data.asset_severity_alerts_data(df)
  df.severity = df.severity.astype("category").cat.set_categories(analyze_data.SEVERITIES)
  df = df.sort_values("severity")

  plt.figure(2)

  plt.scatter(df["severity"], df["alerts"])
  plt.xlabel("Severity")
  plt.ylabel("Alerts")
  plt.title("Asset Alerts per Severity")
  plt.legend(["asset"])

def plot_platform_alerts_assets_data(df):
  df = analyze_data.platform_alerts_assets_data(df)
  x_axis = np.arange(len(df["platform"]))

  plt.figure(3)

  width = 0.40
  plt.bar(x_axis-width/2, df["alerts"], width, label="Alerts")
  plt.bar(x_axis+width/2, df["assets"], width, label="Assets")

  plt.xticks(x_axis, df["platform"])
  plt.xlabel("Platform")
  plt.ylabel("Count")
  plt.title("Alerts and Assets per Platform")
  plt.legend()

def plot_platform_severity_data(df):
  df = analyze_data.platform_severity_percent_data(df)
  x_axis = np.arange(len(df["platform"]))

  plt.figure(4)

  width = 0.15
  plt.bar(x_axis-width*2, df["SAFE"], width, label="SAFE", color="green")
  plt.bar(x_axis-width, df["LOW"], width, label="LOW", color="lime")
  plt.bar(x_axis, df["MEDIUM"], width, label="MEDIUM", color="yellow")
  plt.bar(x_axis+width, df["HIGH"], width, label="HIGH", color="orange")
  plt.bar(x_axis+width*2, df["CRITICAL"], width, label="CRITICAL", color="red")

  plt.xticks(x_axis, df["platform"])
  plt.xlabel("Platform")
  plt.ylabel("Severity %")
  plt.title("Platform Severity Distribution")
  plt.legend()

def plot_alerts_time_data(df):
  plt.figure(5)

  data = df["created_at"].apply(lambda time: pd.to_datetime(time, format="%Y-%m-%dT%H:%M:%S.%fZ"))
  plt.hist(data)

  plt.gcf().autofmt_xdate()
  plt.title("Alerts Over Time")
  plt.legend(["Alerts"])


if __name__ == "__main__":
  df = pd.read_csv("dataset.csv")
  plot_alert_id_alerts_data(df)
  plot_severity_alerts_data(df)
  plot_asset_severity_alerts_data(df)
  plot_platform_alerts_assets_data(df)
  plot_platform_severity_data(df)
  plot_alerts_time_data(df)
  plt.show()
