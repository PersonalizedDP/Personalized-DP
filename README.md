# Personalized DP
Here are the experiments for the paper: Personalized Truncation for Personalized Privacy. 

## Data
The synthetc data are contained inside the notebooks. Real data (Adult) and SQL query results are contained in the folder `./Data`. 

Since github has size limit, the full data is uploaded to: https://drive.google.com/drive/folders/1L_UHEds-ySxB4aFH39DkwssS8m41yFFy?usp=sharing

For TPCH dataset, we use `6` different scales: `0.125,0.25,..,4` which are marked as `_0,_1,..,_5`. For example, 'Q7_0.txt' stores the result of Q7 with scale factor 0.125.


## Codes

The experiments for the count and sum problem are done in notebooks, for details please refer to the comments in `pdp_count.ipynb`  and `pdp_sum.ipynb`.

 The experiments for the query problem are done via the scripts in `./scripts` since they are more time-consuming, where the prefixes like 'naive', 'sample', and 'pdp' indicate different methods. `pdp_query.ipynb` provides a demo of such experiments and do not contain the full information.

## Figures and Results
`figures.ipynb` draws the figures used in the paper.

`./results` stores the results for queries. Here '_uni' indicates the privacy specification follows from the uniform distribution, and otherwise it follows from the Gaussian distribution, which is the default setting.
