from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QAbstractItemView, QTextEdit, QComboBox, QLineEdit
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import QMessageBox

def assign_of_interest(parent):
    selected_indexes = parent.variables_list.selectedIndexes()
    if selected_indexes:
        all_string = True
        for index in selected_indexes:
            type_of_var = index.data().split(" [")[1].replace("]", "")
            if type_of_var != "String":
                all_string = False
                parent.of_interest_var = [index.data()]
                parent.of_interest_model.setStringList(parent.of_interest_var)
                parent.variables_list.model().removeRow(selected_indexes[-1].row())  # Remove from variables list
                show_r_script(parent)
                break
        if all_string:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("All selected variables are of type String. Variable of interest must be of type Numeric.")
            msg.setWindowTitle("Warning")
            msg.exec()

def assign_auxilary(parent):
    selected_indexes = parent.variables_list.selectedIndexes()
    if selected_indexes:
        new_vars = []
        for index in selected_indexes:
            type_of_var = index.data().split(" [")[1].replace("]", "")
            if type_of_var != "String":
                new_vars.append(index.data())
        if not new_vars:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("No valid numeric variables selected. Please select at least one numeric variable.")
            msg.setWindowTitle("Warning")
            msg.exec()
            return
        parent.auxilary_vars = list(set(parent.auxilary_vars + new_vars))  # Add new variables if they are different
        parent.auxilary_model.setStringList(parent.auxilary_vars)
        for index in sorted(selected_indexes, reverse=True):
            parent.variables_list.model().removeRow(index.row())  # Remove from variables list
        show_r_script(parent)

def assign_vardir(parent):
    selected_indexes = parent.variables_list.selectedIndexes()
    if selected_indexes:
        all_string = True
        for index in selected_indexes:
            type_of_var = index.data().split(" [")[1].replace("]", "")
            if type_of_var != "String":
                all_string = False
                parent.vardir_var = [index.data()]
                parent.vardir_model.setStringList(parent.vardir_var)
                parent.variables_list.model().removeRow(selected_indexes[-1].row())  # Remove from variables list
                show_r_script(parent)
                break
        if all_string:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("All selected variables are of type String. Vardir variable must be of type Numeric.")
            msg.setWindowTitle("Warning")
            msg.exec()

def assign_as_factor(parent):
    selected_indexes = parent.variables_list.selectedIndexes()
    if selected_indexes:
        new_vars = []
        for index in selected_indexes:
            new_vars.append(index.data())
        parent.as_factor_var = list(set(parent.as_factor_var + new_vars))  # Add new variables if they are different
        parent.as_factor_model.setStringList(parent.as_factor_var)
        for index in sorted(selected_indexes, reverse=True):
            parent.variables_list.model().removeRow(index.row())  # Remove from variables list
        show_r_script(parent)
        
def assign_domain(parent):
    selected_indexes = parent.variables_list.selectedIndexes()
    if selected_indexes:
        parent.domain_var = [selected_indexes[0].data()]
        parent.domain_model.setStringList(parent.domain_var)
        parent.variables_list.model().removeRow(selected_indexes[0].row())  # Remove from variables list
        show_r_script(parent)

def unassign_variable(parent):
    def remove_selected_items(selected_list, target_list, model):
        selected_items = [index.data() for index in selected_list.selectedIndexes()]
        if selected_items:
            for item in selected_items:
                if item in target_list:
                    target_list.remove(item)
                parent.variables_list.model().insertRow(0)  # Add back to variables list
                parent.variables_list.model().setData(parent.variables_list.model().index(0), item)
            model.setStringList(target_list)  # Update the model
            show_r_script(parent)

    remove_selected_items(parent.of_interest_list, parent.of_interest_var, parent.of_interest_model)
    remove_selected_items(parent.auxilary_list, parent.auxilary_vars, parent.auxilary_model)
    remove_selected_items(parent.vardir_list, parent.vardir_var, parent.vardir_model)
    remove_selected_items(parent.as_factor_list, parent.as_factor_var, parent.as_factor_model)
    remove_selected_items(parent.domain_list, parent.domain_var, parent.domain_model)


def get_selected_variables(parent):
    return parent.of_interest_var, parent.auxilary_vars, parent.vardir_var, parent.as_factor_var

def generate_r_script(parent):
    of_interest_var = f'{parent.of_interest_var[0].split(" [")[0].replace(" ", "_")}' if parent.of_interest_var else '""'
    auxilary_vars = " + ".join([var.split(" [")[0].replace(" ", "_") for var in parent.auxilary_vars]) if parent.auxilary_vars else '""'
    vardir_var = f'{parent.vardir_var[0].split(" [")[0].replace(" ", "_")}' if parent.vardir_var else '""'
    as_factor_var = " + ".join([f'as.factor({var.split(" [")[0].replace(" ", "_")})' for var in parent.as_factor_var]) if parent.as_factor_var else '""'
    domain_var = f'"{parent.domain_var[0].split(" [")[0].replace(" ", "_")}"' if parent.domain_var else 'NULL'
    
    if (auxilary_vars=='""' or auxilary_vars is None) and as_factor_var=='""':
        formula = f'{of_interest_var} ~ 1'
    elif as_factor_var=='""':
        formula = f'{of_interest_var} ~ {auxilary_vars}'
    elif auxilary_vars=='""':
        formula = f'{of_interest_var} ~ {as_factor_var}'
    else:
        formula = f'{of_interest_var} ~ {auxilary_vars} + {as_factor_var}'

    r_script = f'names(data) <- gsub(" ", "_", names(data)); #Replace space with underscore\n'
    r_script += f'formula <- {formula}\n'
    r_script += f'vardir_var <- data["{vardir_var}"]\n'
    if parent.selection_method=="Stepwise":
        parent.selection_method = "both"
    if parent.selection_method and parent.selection_method != "None" and auxilary_vars:
        r_script += f'stepwise_model <- step(formula, direction="{parent.selection_method.lower()}")\n'
        r_script += f'final_formula <- formula(stepwise_model)\n'
        r_script += f'model<-fh(final_formula, vardir="{vardir_var}", combined_data =data, domains={domain_var}, method = "reblupbc", MSE=TRUE, mse_type = "pseudo")'
    else:
        r_script += f'model<-fh(formula, vardir="{vardir_var}", combined_data =data, domains={domain_var}, method = "reblupbc", MSE=TRUE, mse_type = "pseudo")'
    return r_script

def show_r_script(parent):
    r_script = generate_r_script(parent)
    parent.r_script_edit.setText(r_script)

def get_script(parent):
    return parent.r_script_edit.toPlainText()  

def show_options(parent):
    options_dialog = QDialog(parent)
    options_dialog.setWindowTitle("Options")

    layout = QVBoxLayout()

    # method_label = QLabel("Stepwise Selection Method:")
    # layout.addWidget(method_label)

    # parent.method_combo = QComboBox()
    # parent.method_combo.addItems(["None", "Stepwise", "Forward", "Backward"])
    # layout.addWidget(parent.method_combo)

    button_layout = QHBoxLayout()
    ok_button = QPushButton("OK")
    cancel_button = QPushButton("Cancel")
    button_layout.addWidget(ok_button)
    button_layout.addWidget(cancel_button)

    layout.addLayout(button_layout)

    options_dialog.setLayout(layout)

    ok_button.clicked.connect(lambda: set_selection_method(parent, options_dialog))
    cancel_button.clicked.connect(options_dialog.reject)

    options_dialog.exec()

def set_selection_method(parent, dialog):
    # parent.selection_method = parent.method_combo.currentText()
    dialog.accept()
    show_r_script(parent)

import unittest
from unittest.mock import MagicMock

class TestUnassignVariable(unittest.TestCase):

    def setUp(self):
        self.parent = MagicMock()
        self.parent.of_interest_var = ["var1 [Numeric]"]
        self.parent.auxilary_vars = ["var2 [Numeric]", "var3 [Numeric]"]
        self.parent.vardir_var = ["var4 [Numeric]"]
        self.parent.as_factor_var = ["var5 [String]"]
        self.parent.domain_var = ["var6 [Numeric]"]

    def test_unassign_of_interest_variable(self):
        self.parent.of_interest_list.selectedIndexes.return_value = [MagicMock(data=lambda: "var1 [Numeric]")]
        unassign_variable(self.parent)
        self.assertEqual(self.parent.of_interest_var, [])
        self.parent.of_interest_model.setStringList.assert_called_with([])
        self.parent.variables_list.model().insertRow.assert_called_with(0)
        self.parent.variables_list.model().setData.assert_called_with(self.parent.variables_list.model().index(0), "var1 [Numeric]")

    def test_unassign_auxilary_variable(self):
        self.parent.auxilary_list.selectedIndexes.return_value = [MagicMock(data=lambda: "var2 [Numeric]")]
        unassign_variable(self.parent)
        self.assertEqual(self.parent.auxilary_vars, ["var3 [Numeric]"])
        self.parent.auxilary_model.setStringList.assert_called_with(["var3 [Numeric]"])
        self.parent.variables_list.model().insertRow.assert_called_with(0)
        self.parent.variables_list.model().setData.assert_called_with(self.parent.variables_list.model().index(0), "var2 [Numeric]")

    def test_unassign_vardir_variable(self):
        self.parent.vardir_list.selectedIndexes.return_value = [MagicMock(data=lambda: "var4 [Numeric]")]
        unassign_variable(self.parent)
        self.assertEqual(self.parent.vardir_var, [])
        self.parent.vardir_model.setStringList.assert_called_with([])
        self.parent.variables_list.model().insertRow.assert_called_with(0)
        self.parent.variables_list.model().setData.assert_called_with(self.parent.variables_list.model().index(0), "var4 [Numeric]")

    def test_unassign_as_factor_variable(self):
        self.parent.as_factor_list.selectedIndexes.return_value = [MagicMock(data=lambda: "var5 [String]")]
        unassign_variable(self.parent)
        self.assertEqual(self.parent.as_factor_var, [])
        self.parent.as_factor_model.setStringList.assert_called_with([])
        self.parent.variables_list.model().insertRow.assert_called_with(0)
        self.parent.variables_list.model().setData.assert_called_with(self.parent.variables_list.model().index(0), "var5 [String]")

    def test_unassign_domain_variable(self):
        self.parent.domain_list.selectedIndexes.return_value = [MagicMock(data=lambda: "var6 [Numeric]")]
        unassign_variable(self.parent)
        self.assertEqual(self.parent.domain_var, [])
        self.parent.domain_model.setStringList.assert_called_with([])
        self.parent.variables_list.model().insertRow.assert_called_with(0)

if __name__ == '__main__':
    unittest.main()