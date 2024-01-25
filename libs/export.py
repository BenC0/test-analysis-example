import json, re, os
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
import libs.analysis as analysis
import pandas as pd

generated_full_palette = sns.color_palette([ "#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087", "#f95d6a", "#ff7c43", "#ffa600", ], 8)
generated_palette = sns.color_palette(["#003f5c", "#a05195", "#ffa600"], 3)
generated_small_palette = sns.color_palette(["#003f5c", "#ffa600"], 2)
colour_map = {
    "Control": "#003f5c",
    "Variation 1": "#58508d",
    "Variation 2": "#bc5090",
    "Variation 3": "#ff6361",
    "Variation 4": "#ffa600",
}
sns.set_theme(style="darkgrid")

def output_metric_to_config(slides, id="PAH000"):
    config_path = "./slide_config.json"
    config = {
        "id": id,
        "name": "Data Report",
        "content": slides
    }
    config_file = open(config_path, "w+")
    json.dump(config, config_file)
    return config

def generate_divider_slide(title=""):
    return {
        "name": title,
        "type": "Divider Slide",
        "layout": "Divider Slide 1",
        "title": title,
    }

def generate_notes_slide(title="", content=""):
    return {
        "name": title,
        "type": "Notes Slide",
        "layout": "Long Form Messaging 1",
        "title": title,
        "content": content,
    }

def generate_report_info_slide(title="", content=""):
    return {
        "name": title,
        "type": "Report Info Slide",
        "layout": "Long Form Messaging 1",
        "title": title,
        "content": content,
    }

def generate_title_slide(title="", subtitle = ""):
    return {
        "name": title,
        "type": "Title Slide",
        "layout": "Title Slide 2",
        "title": title,
        "subtitle": subtitle
    }

def generate_metric_slide(title="", segment = "", data = pd.DataFrame(data=np.zeros(shape=(2, 2))), image_path="", footer=""):
    return {
        "name": title,
        "type": "Title Slide",
        "layout": "Chart and Data",
        "title": title,
        "segment": segment,
        "data": np.vstack([data.columns, data.to_numpy()]).tolist(),
        "image_path": image_path,
        "footer": footer,
    }

def generate_heatmap_slide(title="", segment = "", image_path=""):
    return {
        "name": title,
        "type": "Heatmap Slide",
        "layout": "Heatmap",
        "title": title,
        "segment": segment,
        "image_path": image_path
    }

def generate_chart_slide(title="", segment = "", image_path=""):
    return {
        "name": title,
        "type": "Chart Only",
        "layout": "Chart Only",
        "title": title,
        "segment": segment,
        "image_path": image_path
    }

def format_perc_to_ratio(x):
    return format_float(x/100)
    
def format_perc_to_ratio_float_dtype(x):
    return float(format_float(x/100))

def format_perc(x):
    return f"{x:.2f}%"

def format_float(x):
    return f"{x:0,.2f}"

def format_int(x):
    return f"{x:0,.0f}"

def format_rev(x):
    return f"£{x:0,.2f}"

def format_series(d, format_map = None, rename_map = None, transpose=True):
    data = d.copy()
    if type(format_map) != type(None):
        if "segment" in data.columns:
            data = data.drop("segment", axis=1)
        for column in data.columns:
            if column in format_map:
                data[column] = data[column].apply(format_map[column])
    if type(rename_map) != type(None):
        data.rename(columns = rename_map, inplace=True)
    if transpose:
        data = transpose_data(data)
        return data.reset_index(names="")
    return data

def transpose_data(data):
    data = data.set_index("Variant").T
    data.columns.name=""
    return data

def visualise(data, kpi, name, ylim=.8, fmt="%.2f%%", extra_title="", hide=True, palette=colour_map):
    plt.subplots(1, 1, figsize=(8, 8))
    chart = sns.barplot(data=data, x="Variant", y=kpi, palette=palette)
    if isinstance(ylim, (float, int)):
        chart.set_ylim(0, ylim)
    elif isinstance(ylim, tuple):
        chart.set_ylim(ylim[0], ylim[1])
    chart.set_xlabel("")
    chart.set_ylabel("")
    chart.set_title(f"{kpi} {extra_title}")
    for container in chart.containers:
        chart.bar_label(container, fmt=fmt)
    plt.tight_layout()
    if not os.path.exists(f"./visualisations/"):
        os.makedirs(f"./visualisations/")
    plt.savefig(f"./visualisations/{name}.png", format="png")
    if hide:
        plt.close()