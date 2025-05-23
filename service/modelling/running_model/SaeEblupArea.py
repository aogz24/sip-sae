import polars as pl
from PyQt6.QtWidgets import QMessageBox
from rpy2.rinterface_lib.embedded import RRuntimeError
from service.modelling.running_model.convert_df import convert_df

def run_model_eblup_area(parent):
    """
    Runs the EBLUP (Empirical Best Linear Unbiased Prediction) area model using the provided parent object.
    Parameters:
    parent (object): The parent object that contains necessary methods and attributes for running the model.
                     It should have the following methods and attributes:
                     - activate_R(): Method to activate R environment.
                     - model1.get_data(): Method to get the data for the model.
                     - r_script: An R script to be executed.
    Returns:
    tuple: A tuple containing:
           - result (str): The result of the model execution or error message.
           - error (bool): A flag indicating whether an error occurred.
           - df (polars.DataFrame or None): A DataFrame containing the estimated values, MSE, and RSE if the model runs successfully, otherwise None.
    """
    
    import rpy2.robjects as ro
    parent.activate_R()
    df = parent.model1.get_data()
    df = df.drop_nulls()
    result = ""
    error = False
    convert_df(df, parent)
    try:
        ro.r('suppressMessages(library(sae))')
        ro.r('data <- as.data.frame(r_df)')
        try:
            ro.r(parent.r_script)  # Menjalankan skrip R
        except RRuntimeError as e:
            result = str(e)
            error = True
            return result, error, None
        ro.r('estimated_value <- model$est$eblup\n mse <- model$mse')
        result_str = ro.r('capture.output(print(model))')
        result = "\n".join(result_str)
        estimated_value = ro.conversion.rpy2py(ro.globalenv['estimated_value'])
        mse = ro.conversion.rpy2py(ro.globalenv['mse'])
        vardir_var = ro.conversion.rpy2py(ro.globalenv['vardir_var'])
        estimated_value = estimated_value.flatten()
        vardir_var = vardir_var.to_numpy()[:, 0]
        rse = mse**0.5/estimated_value*100
        df = pl.DataFrame({
            'Eblup': estimated_value,
            'MSE': mse,
            'RSE (%)': rse})
        error = False
        return result, error, df
        
    except Exception as e:
        error = True
        return str(e), error, None