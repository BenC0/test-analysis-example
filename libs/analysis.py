import os
import re
import pandas as pd
import numpy as np

from datetime import datetime
from scipy.stats import beta
from libs.calc_prob import calc_prob_between

import matplotlib.pyplot as plt
import seaborn as sns
generated_full_palette = sns.color_palette([ "#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087", "#f95d6a", "#ff7c43", "#ffa600", ], 8)
generated_palette = sns.color_palette(["#003f5c", "#a05195", "#ffa600"], 3)
generated_small_palette = sns.color_palette(["#003f5c", "#ffa600"], 2)
sns.set_theme(style="darkgrid")

def bayes(data, impressions="Sessions", goal="Transactions", control="Control", variant="Variation 1", name=None):
    control = data[data["optimisation_variant"] == control].copy()
    test = data[data["optimisation_variant"] == variant].copy()
    if control.shape[0] == 0 or control[impressions].sum() == 0 or control[goal].sum() == 0:
        print(f"No Control Data, goal: {goal}, impressions: {impressions}")
        return {"variant": variant, "metric": name, "Impact": 0, "Chance of being best": 0 }
    if test.shape[0] == 0 or test[impressions].sum() == 0 or test[goal].sum() == 0:
        print(f"No Variant Data, goal: {goal}, impressions: {impressions}")
        return {"variant": variant, "metric": name, "Impact": 0, "Chance of being best": 0 }
    # This is the known data: imporessions and conversions for the Control and Test set
    imps_ctrl = control[impressions].mean()
    convs_ctrl = control[goal].mean()
    imps_test = test[impressions].mean()
    convs_test = test[goal].mean()
    # here we create the Beta functions for the two sets
    a_C, b_C = convs_ctrl+1, imps_ctrl-convs_ctrl+1
    beta_C = beta(a_C, b_C)
    a_T, b_T = convs_test+1, imps_test-convs_test+1
    beta_T = beta(a_T, b_T)
    #calculating the lift
    cr_test = convs_test.mean() / imps_test.mean()
    cr_ctrl = convs_ctrl.mean() / imps_ctrl.mean()
    if cr_ctrl == cr_test or cr_ctrl == 0 or cr_test == 0:
        lift = 0
    else:
        lift=(cr_test-cr_ctrl)/cr_ctrl
    #calculating the probability for Test to be better than Control
    prob=calc_prob_between(beta_T, beta_C)
    # prob=calc_prob_between(beta_T, beta_C)
    if name == None:
        name = goal
    return {"variant": variant, "metric": name, "Impact": lift*100, "Chance of being best": prob*100 }

def build_metric_object(order, name, display_name, previous_step):
    return {
        "order": order,
        "name": name,
        "display_name": display_name,
        "previous_step": previous_step,
    }

def calc_rate(src, metric, impressions="impressions", is_revenue = False, metric_name=False):
    if metric_name == False:
        metric_name = metric
    if is_revenue is True:
        inferred_name = re.sub(r"_|revenue", "", metric).capitalize()
        rate = f"Avg. {inferred_name} Value"
        src[rate] = src[metric] / src[impressions]
    else:
        src[f"{metric_name} Rate"] = (src[metric] / src[impressions]) * 100

def calc_sig(src, metric, impressions="impressions", metric_name=False, control_name = "Control"):
    if metric_name == False:
        metric_name = metric
    impact = []
    sig = []
    for variant in src.optimisation_variant:
        sig_calced = bayes(src, variant=variant, impressions=impressions, goal=metric, control=control_name)
        sig.append(sig_calced['Chance of being best'])
        impact.append(sig_calced['Impact'])
    src[f"{metric_name} Significance"] = sig
    src[f"{metric_name} Impact"] = impact

def summarise_test(details = None, data = None, metrics = [], dimensions = [], calc_significance = True, control_name = "Control"):
    if type(details) != type(None):
        print(f"Test: {details.name.values[0]}")
        print(f"Description: {details.description.values[0]}")
        print(f"Targeting: {details.targeting.values[0]}")
        print(f"Category: {details.category.values[0]}")
        print(f"Device: {details.device.values[0]}")
        print(f"Ecommerce: {details.is_ecommerce.values[0]}, Polestar: {details.is_polestar.values[0]}")
    if type(data) != type(None):
        metric_names = []
        for metric in metrics:
            if metric["name"] not in metric_names:
                metric_names.append(metric["name"])
        control_metric_names = [f"control_{metric}" for metric in metric_names]
        all_dimensions = ["optimisation_variant"] + dimensions
        summary = data[all_dimensions + metric_names + control_metric_names].groupby(by=all_dimensions).sum()
        summary = summary.reset_index()
        for metric in metrics:
            summary[metric["display_name"]] = summary[metric["name"]]
            if metric["previous_step"] != None:
                is_revenue = "revenue" in metric["name"].lower()
                if calc_significance:
                    calc_sig(summary, metric["name"], metric["previous_step"], metric["display_name"], control_name = control_name)
                calc_rate(summary, metric["name"], metric["previous_step"], is_revenue=is_revenue, metric_name=metric["display_name"])
        summary.drop(metric_names + control_metric_names, axis=1, inplace=True)
        return summary
    return None

def visualise_summary(data, date = "", name = ""):
    sig = data[[col for col in data.columns if "Significance" in col]].copy()
    sig.columns.name = ""
    sig.columns = [col.replace(" Significance", "") for col in sig.columns]
    sig.reset_index(inplace=True)
    sig = sig.melt(id_vars="optimisation_variant", var_name="Metric", value_name="Significance")

    imp = data[[col for col in data.columns if "Impact" in col]].copy()
    imp.columns.name = ""
    imp.columns = [col.replace(" impnificance", "") for col in imp.columns]
    imp.reset_index(inplace=True)
    imp = imp.melt(id_vars="optimisation_variant", var_name="Metric", value_name="Impact")

    rate = data[[col for col in data.columns if " Rate" in col]].copy()
    rate.columns.name = ""
    rate.columns = [col.replace(" Rate", "") for col in rate.columns]
    rate.reset_index(inplace=True)
    rate = rate.melt(id_vars="optimisation_variant", var_name="Metric", value_name="Rate")
    
    fig, ax = plt.subplots(3, 1, figsize=(20, 15))
    fig.suptitle(name, fontsize=16)
    rate_bp = sns.barplot(data=rate, x="Metric", y="Rate", hue="optimisation_variant", palette=generated_palette, ax=ax[0])
    imp_bp = sns.barplot(data=imp, x="Metric", y="Impact", hue="optimisation_variant", palette=generated_palette, ax=ax[1])
    sig_bp = sns.barplot(data=sig, x="Metric", y="Significance", hue="optimisation_variant", palette=generated_palette, ax=ax[2])
    ax[0].set_title("Rate", pad=10)
    ax[1].set_title("Relative Impact", pad=10)
    ax[2].set(ylim=(0, 100))
    ax[2].set_title("Chance of being best", pad=10)
    for bp in [imp_bp, sig_bp, rate_bp]:
        bp.axhline(0, c="red")
        for container in bp.containers:
            bp.bar_label(container, fmt="%.2f%%")
    plt.tight_layout()
    if not os.path.exists(f"./visualisations/{date}/"):
        os.makedirs(f"./visualisations/{date}/")
    if name != None:
        plt.savefig(f"./visualisations/{date}/{name}.png", format="png")

DEFAULT_METRICS = [
    build_metric_object(0, "impressions", "Impressions", None),
    build_metric_object(1, "page_views", "Page views", "impressions"),
    build_metric_object(2, "view_search_results", "SRP progression", "page_views"),
    build_metric_object(3, "view_item_lists", "PLP progression", "page_views"),
    build_metric_object(4, "view_items", "PDP progression", "page_views"),
    build_metric_object(5, "add_to_carts", "Add to cart rate", "view_items"),
    build_metric_object(6, "view_carts", "Cart progression", "page_views"),
    build_metric_object(7, "select_fulfillment", "Checkout delivery progression", "view_carts"),
    build_metric_object(8, "select_payment", "Checkout payment progression", "select_fulfillment"),
    build_metric_object(9, "purchases", "Purchases", "select_payment"),
    build_metric_object(10, "transaction_revenue", "Transaction Revenue", "purchases"),
]