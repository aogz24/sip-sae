import os
import polars as pl
from PyQt6.QtWidgets import QMessageBox
import rpy2.robjects as ro
import rpy2.robjects.lib.grdevices as grdevices

def run_normality_test(parent):
    """
    Runs a normality test on the combined data from two models in the parent object.
    This function performs the following steps:
    1. Activates the R environment.
    2. Retrieves data from two models in the parent object and concatenates them horizontally.
    3. Drops any rows with null values.
    4. Converts the concatenated data to an R dataframe.
    5. Executes an R script provided by the parent object to perform normality tests.
    6. Collects the results of the normality tests and any generated plots.
    Parameters:
    parent (object): An object that contains the following attributes:
        - activate_R(): A method to activate the R environment.
        - model1: An object with a get_data() method that returns a dataframe.
        - model2: An object with a get_data() method that returns a dataframe.
        - r_script (str): An R script to be executed.
        - selected_columns (list): A list of column names to be tested for normality.
        - result (str): A string to store the results of the normality tests.
        - plot (list): A list to store the paths of generated plots.
        - error (bool): A boolean to indicate if an error occurred.
    Raises:
    Exception: If any error occurs during the execution of the R script or data processing.
    """
    
    import rpy2.robjects as ro
    import rpy2_arrow.polars as rpy2polars
    
    parent.activate_R()
    df1 = parent.model1.get_data()
    df2 = parent.model2.get_data()
    df = pl.concat([df1, df2], how="horizontal")
    df = df.drop_nulls() 

    with rpy2polars.converter.context() as cv_ctx:
        r_df = rpy2polars.converter.py2rpy(df)
        ro.globalenv['r_df'] = r_df

    try:
        ro.r('rm(list=ls()[ls() != "r_df"])')
        ro.r('suppressMessages(library(nortest))')
        ro.r('suppressMessages(library(tseries))')
        ro.r('suppressMessages(library(ggplot2))')

        ro.r('data <- as.data.frame(r_df)')

        script = parent.r_script
        ro.r(script)

        selected_vars = parent.selected_columns
        result_str = ""
        plot_paths = []  
        test_names = ["shapiro", "jarque", "lilliefors"]

        for var in selected_vars:
            safe_var = var.replace(" ", "_")  

            for test in test_names:
                result_key = f"normality_results_{safe_var}_{test}"
                if ro.r(f"exists('{result_key}')")[0]:
                    result = ro.r(f"capture.output(print({result_key}))")
                    result_str += f"{var} - {test} Test:\n" + "\n".join(result) + "\n"

            # Menyimpan plot jika ada
            for plot_type in ["histogram", "qqplot"]:
                plot_name = f"{plot_type}_{safe_var}"
                if ro.r(f"exists('{plot_name}')")[0]:
                    plot_path = f"temp_{plot_name}.png"
                    grdevices.png(file=plot_path, width=800, height=600)
                    ro.r(f"print({plot_name})")
                    grdevices.dev_off()
                    plot_paths.append(plot_path)

        parent.result = result_str
        parent.plot = plot_paths 
        
    except Exception as e:
        parent.result = str(e)
        parent.error = True
