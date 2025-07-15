# VariableSelector

The `VariableSelector` is a centralized component designed to manage shared inputs and states across different modules in the application. It ensures that updates to a variable (e.g., the year) are reflected consistently across all modules, promoting synchronization and modularity.

This flexibility allows the framework to adapt to different implementations and variable requirements.

## The problem

The problem that needed solving was how we could make sure all modules communicate and show data for the same periods, while keeping each module isolated from eachother.

In addition to this, we needed a way for users to define which information should be shared between modules, and how. And without making the configuration too complex.

## The solution

The solution was the VariableSelector.

It consists of two classes:

### VariableSelectorOption

The VariableSelectorOption consists of a title and id*. The title is what is shown in the interface, while id is used for callbacks.

When initialized, it adds itself to a list used later for coordinating modules through the VariableSelector class. It also makes sure that there are no duplicates.

To simplify initialization we have created the function `set_variables()` which takes a list of strings and sets up each as an option.

* It also has a type, but for now it only supports text.

### VariableSelector

This class will be used to set up most interactions between modules. It contains a class variable containing all currently initialized options and several methods to access them.

During the app setup the main_layout function will create a variable selector module in the app layout

Ideally each module should define its own VariableSelector instance with their own inputs and states specified.

## How it is used
