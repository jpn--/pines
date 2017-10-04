import numpy
import pandas

def count_and_share(data, groupby_cols, discrete_col, rounding=1):
    """
    From source data, generate a tally of unique values and then shares by category.

    Parameters
    ----------
    data : pandas.DataFrame
    groupby_cols : str or iterable
        Name of the column[s] in `data` containing the categories.
    discrete_col : str
        Name of the column in `data` containing the discrete response to analyze.
    rounding : int, optional
        Round the shares to this many decimal places, defaults to 1

    Returns
    -------
    pandas.DataFrame
    """
    f = pandas.DataFrame(data.groupby(list(groupby_cols)+[discrete_col]).apply(len), columns=[discrete_col+'_Count'])
    return calculate_shares(f, groupby_cols, discrete_col, rounding)


def calculate_shares(count_data, groupby_cols, discrete_col, rounding=1):
    bucketshare = lambda x: numpy.round(x / x.sum() * 100, rounding)
    if groupby_cols:
        count_data[discrete_col+'_Share'] = count_data.groupby(groupby_cols).transform(bucketshare)
    else:
        count_data[discrete_col + '_Share'] = count_data.transform(bucketshare)
    return count_data


def count_and_share_iterative(data_iterator, groupby_cols, discrete_col, rounding=1, live_update=False):
    f_total = None
    for n,d in enumerate(data_iterator):
        if isinstance(d, tuple):
            pct_complete = d[1]
            d = d[0]
        else:
            pct_complete =  None
        f = count_and_share(d, groupby_cols, discrete_col, rounding)
        if f_total is None:
            f_total = f
        else:
            f_total = f_total.add(f, fill_value=0)
        if live_update:
            from IPython import display
            display.clear_output(wait=True)
            if pct_complete:
                print(f"{pct_complete*100:.2f}% complete")
            else:
                print("To chunk",n)
            f_total = calculate_shares(f_total, groupby_cols, discrete_col, rounding)
            display.display_html(f_total)
    if not live_update:
        f_total = calculate_shares(f_total, groupby_cols, discrete_col, rounding)
    return f_total