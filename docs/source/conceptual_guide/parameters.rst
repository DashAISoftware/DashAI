.. _parameters:

Parameters Schemas
==================

As we saw in section :ref:`components <components>`, all classes that can be used in the software flow are called *components*, some of those
classes can be configured, for example in a *Support Vector Machine* we can change the regularization parameter **C** to any positive number
to get better results. But if we set the **C** parameter to a negative number the model will not work correctly and will probably fail.

So to work with parameters it is necessary not only to have the possibility to set the values, but also to check whether the given value is
compatible with the component.

To solve both problems **DashAI** implements *Parameters Schemas*, which consist of an interface where the component declares all its parameters
and the constraints around them.

Parameter schemes have the following steps in the software: **Declaration**, **Display**, **Validation** and **Usage**.

Declaration
-----------

The declaration step consists of building the component parameter interface, for this we must create the *Component Schema* and inside it
declare all the component parameters.

The *Component Schema* is built by creating a new class and making it inherit from the *BaseSchema* class. The class also needs a docstring with
the component summary to be used as the component description.

To declare component parameters we need to add fields to *Component Schema* and type them. To write the parameters we need to use the typing
functions declared in *DashAI/back/core/schema_fields*. The available parameter types are as follows:

* *bool_field* to declare a boolean parameter.
* *component_field* to declare a parameter that spects a component.
* *enum_field* to declare a parameter that spects an string from an especific enum.
* *float_field* to declare a floating-point number parameter.
* *int_field* to declare an integer parameter.
* *none_field* to declare a optional parameter, i.e. that it's value can be none.
* *optmizer_float_field* to declare an optimizable floating-point number parameter.
* *optimizer_int_field* to declare an optmizable integer parameter.
* *string_field* to declare a string parameter.
* *union_field* to declare that the parameter can have any of two different types.

To use the above functions it is necessary to first call the *schema_field* function and pass the type functions as the first parameter. It is also
mandatory to pass a placeholder, i.e. the default value of the field, and the field description, a brief summary of what is controlled by the
parameter and its constraints.

The type functions receive as optional parameters some values that act as constraints on the parameter, e.g. to construct the **C** parameter
seen above it is necessary to set the *gt* (greater than) parameter of the *int_field* to 0 because the parameter can only be set to
positive integer values.

Display
-------

The *Component Schema* defined in the last step is transformed into a JSON schema (a dictionary-like structure) using the *get_schema*
method defined in the **ConfigObject** class. This class is inherited by all configurable components in **DashAI**.

The JSON schema is stored in the *component registry* and then passed to the frontend via the **GET** */component* endpoint.

The GUI uses the JSON schema to create a form with all the component parameters.

Each field is mapped into an input react component. Each input has the name of the parameter, a default value and a question mark icon to see
the description of the parameter.

The react components presented in the frontend are the following:

- **BooleanInput** for *bool_field*.
- **ClassInput** for *component_field*.
- **SelectInput** for *enum_field*.
- **NumberInput** for *float_field*.
- **IntegerInput** for *int_field*.
- **NumberInputOptimize** for *optimizer_float_field*.
- **IntegerInputOptimize** for *optimizer_int_field*.
- **TextInput** for *string_field*.


Validation
----------

The form generated in the graphical interface receives the inputs given by the user, i.e. the values for each parameter, and validates whether
they follow the types and constraints of the parameters.

If any of the values is not compatible with its parameter the frontend does not allow the user to submit the form until the problem is fixed.

When all parameters are valid, the frontend sends the parameters to the backend, where they are stored along with their component.

Later, before the component is used, the backend validates the data again against the JSON schema. If the data is invalid a *ValidationError*
is generated, which stops the process and logs the error.

Usage
-----

After validation and before instantiating the component, the parameters are postprocessed to generate the data that the component expects.

For now the only postprocessing that is done is the transformation of the *component_field* into the selected component. This is because the
*component_field* is a dictionary with the fields *component*, which indicates the name of the component, and *parameters*, which indicates
the parameter values of the selected component.

The main component does not expect a dictionary as a parameter, it expects the actual component selected by the user.
This transformation is performed by the *fill_objects* function.

The parameters are then passed to the main component and the flow ends.
