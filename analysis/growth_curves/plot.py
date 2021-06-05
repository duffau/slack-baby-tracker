import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as ss
import numpy as np
from labellines import labelLines

weight_to_age = pd.read_csv("../../data/growth-curves/weianthro.txt", sep="\t")

ax = weight_to_age[weight_to_age.sex == 1].plot(
    x="age",
    y="m",
    lw=1,
    color="blue",
    title=f"WHO weight to age curves",
    ylabel="weight (kg)",
    xlabel="age (days)",
    label="boy"
)
weight_to_age[weight_to_age.sex == 2].plot(
    x="age",
    y="m",
    lw=1,
    color="red",
    title=f"WHO weight to age curves",
    ylabel="weight (kg)",
    xlabel="age (days)",
    label="girl",
    ax=ax
)
labelLines(plt.gca().get_lines(), zorder=2.5)
ax.get_legend().remove()
plt.tight_layout()
plt.savefig(f"weight_to_age_sexes.png")
plt.close()


for sex in 1, 2:

    df = weight_to_age[weight_to_age.sex == sex].copy()
    S, M, L = np.array(df.s), np.array(df.m), np.array(df.l)

    def confidence(age, alpha, s=S, m=M, l=L):
        z = ss.norm.ppf(alpha, loc=0, scale=1)
        # age = int(age)
        return M[age] * (1 + L[age] * S[age] * z) ** (1 / L[age])

    df["p5"] = confidence(df.age, alpha=0.05)*1000
    df["p25"] = confidence(df.age, alpha=0.25)*1000
    df["p50"] = confidence(df.age, alpha=0.5)*1000
    df["p75"] = confidence(df.age, alpha=0.75)*1000
    df["p95"] = confidence(df.age, alpha=0.95)*1000

    sex_name = ["boy", "girl"][sex - 1]
    df.to_csv(f"../../data/growth-curves/weianthro_{sex_name}.csv")

    ax = df.plot(
        x="age",
        y=["p5", "p25", "p50", "p75", "p95"],
        style=["--", "--", "-", "--", "--"],
        lw=1,
        color="black",
        title=f"WHO weight to age curves: {sex_name}",
        ylabel="weight (g)",
        xlabel="age (days)",
    )
    ax.get_legend().remove()
    labelLines(plt.gca().get_lines(), zorder=2.5)
    plt.tight_layout()
    plt.savefig(f"weight_to_age_{sex_name}.png")
