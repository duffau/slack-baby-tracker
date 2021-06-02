import pandas as pd
import statsmodels.api as sm
from patsy import dmatrices

df = pd.DataFrame()

y, X = dmatrices(
    "Lottery ~ Literacy + Wealth + Region", data=df, return_type="dataframe"
)
mod = sm.OLS(y, X)
res = mod.fit()
print(res.summary())
