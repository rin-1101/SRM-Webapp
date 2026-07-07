from okada import SQL
import pandas as pd

loader = SQL("datamart").get_loader()



def get_loyalty_df():
    loyalty = loader.load_data("SELECT *, CASE WHEN 12moactive = 'Active' THEN unique_pid_count ELSE 0 END AS active FROM dws.dws_mkt_loyaltydb")
    loygrp_sort = ["Prime", "Elite", "Premium", "Supreme", "Maharlika", "Okada VIP"]
    nat_sort = ["Filipino", "Chinese", "NEA", "SEA", "Others"]
    # Convert 'loygrp' to a categorical type with the specified order
    loyalty["loygrp"] = pd.Categorical(loyalty["loygrp"], categories=loygrp_sort, ordered=True)
    loyalty["natgrp"] = pd.Categorical(loyalty["natgrp"], categories=nat_sort, ordered=True)
    return loyalty



def calculate_percentages(df, grouper, count_col="unique_pid_count", active_col="active"):
    # Perform the groupby operation and reset the index
    result = df.groupby(grouper)[[count_col, active_col]].sum().sort_index().reset_index()

    # Add a total row
    total_row = pd.DataFrame({
        grouper: ["Total"], 
        count_col: [result[count_col].sum()],
        active_col: [result[active_col].sum()]
    })
    result_with_total = pd.concat([result, total_row], ignore_index=True)

    # Calculate % Total and % Active
    result_with_total["% Total"] = (result_with_total[count_col] / result_with_total.loc[result_with_total[grouper] == "Total", count_col].values[0]) * 100
    result_with_total["% Active"] = (result_with_total[active_col] / result_with_total[count_col]) * 100

    return result_with_total.drop("active",axis=1)

# Example usage:
# result_with_total = calculate_percentages(loyalty[loyalty["12moactive"]=="Inactive"], "loygrp")
# result_with_total
