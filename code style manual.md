# Code Style Manual

This manual outlines coding style guidelines to ensure consistency, readability, and maintainability across the codebase. Following these practices will enhance collaboration and code quality. The main guidelines must be followed from PEP 8 – Style Guide for Python Code.

---

## 1. Code Structure and Organization

### 1.1 Import Statements
- **Order**: Organize imports into three sections, separated by a blank line:
  1. Standard library imports
  2. Third-party imports
  3. Local application/library-specific imports

- **Example**:
  ```python
  import os
  import sys

  import requests
  import pandas as pd

  from mymodule import settings
  from mymodule.utils import log_error
  ```

### 1.2 Functions
- **Separation**: Place two blank lines between function definitions to visually separate them.
  
- **Documentation**: Each function must include a docstring that:
  - Explains its purpose.
  - Describes parameters (including their types).
  - Specifies return values and types.

- **Logic Separation**: Within functions:
  - Use a blank line to separate distinct logical steps.
  - Include a comment explaining each step.

- **Return Values**: Every function should always return something:
  - Return the main parameter if applicable.
  - Otherwise, return `True`.
  - If neither applies, return `None`.

- **Example**:
  ```python
  def calculate_total_cost(price, quantity):
      """
      Calculates the total cost.

      Parameters:
      - price (float): The price per item.
      - quantity (int): The number of items.

      Returns:
      float: The total cost.
      """
      total_cost = price * quantity  # Calculate the total cost
      return total_cost  # Return the calculated total cost
  ```

## 2. Naming Conventions

### 2.1 Variables and Functions
- **Convention**: Use `snake_case` for naming variables and functions.
- **Descriptive Names**: Names should clearly convey their purpose or action.
- **Example**:
  ```python
  def get_user_age(user):
      user_age = user.get('age')
      return user_age
  ```

### 2.2 Constants
- **Convention**: Use `UPPER_SNAKE_CASE` for constants.
- **Placement**: Define constants at the beginning of the file or within a configuration module.
- **Example**:
  ```python
  MAX_RETRIES = 3
  TIMEOUT_SECONDS = 30
  ```

### 2.3 Classes
- **Convention**: Use `CamelCase` for class names.
- **Naming**: Class names should be nouns or noun phrases that describe the entity they represent.
- **Example**:
  ```python
  class DataProcessor:
      pass
  ```

### 2.4 Best Practices for Naming
- **Clarity and Descriptiveness**: Choose names that clearly describe the entity’s purpose or function. Avoid vague or generic names.
  - **Example**: Use `user_age` instead of `x`, and `temporary_file` instead of `temp`.

- **Consistency**: Follow consistent naming patterns throughout your codebase.
  - **Example**: Use `get_` as a prefix for retrieval functions (`get_user_name()`), and `is_` or `has_` for Boolean functions (`is_valid()`, `has_permission()`).

- **Avoid Abbreviations**: Use full words unless the abbreviation is widely recognized.
  - **Example**: Use `calculate_total` instead of `calc_total`, and `employee_record` instead of `emp_rec`.

- **Pronounceable Names**: Names should be easy to read and pronounce.
  - **Example**: `database_connection` is better than `db_conn`, and `average_salary` is better than `avg_sal`.

- **Avoid Similar Names**: Avoid names that are similar but differ slightly.
  - **Example**: Avoid `data` and `datum` in the same scope, and avoid `user_name` and `user_names` if they represent different things.

- **Reflect the Variable's Role**: Name variables based on their role within the scope.
  - **Example**: Use `current_user` instead of `u` when iterating over users.

- **Use Contextual Naming**: Names should be self-explanatory within their context, reducing the need for additional comments.
  - **Example**: `process_transaction()` is self-explanatory, while `calculate_tax()` clearly explains its function.

- **Consider Future Changes**: Choose names that will remain meaningful as the code evolves.
  - **Example**: Use `customer_list` instead of `customer_array` to accommodate future changes in data structure.

- **Avoid Negations in Boolean Names**: Boolean variables and function names should use positive terms to simplify logic.
  - **Example**: Use `is_active` instead of `is_not_inactive`, and `has_access` instead of `no_access`.

- **Length of Names**: Strike a balance between being descriptive and concise.
  - **Example**: `total_price` is a good balance, while `tp` is too short and `total_price_of_all_items_in_cart` is too long.

## 3. Comments and Documentation

### 3.1 Docstrings
- **Placement**: Use docstrings for all public modules, functions, classes, and methods.
- **Format**: Use triple double quotes (`"""`) for docstrings. The first line should be a concise summary, followed by a more detailed explanation if needed.
- **Parameters and Returns**: Document all parameters and return values, including types.

- **Example**:
  ```python
  def connect_to_database(db_name: str) -> sqlite3.Connection:
      """
      Connects to the specified SQLite database.

      Parameters:
      - db_name (str): The name of the database file.

      Returns:
      sqlite3.Connection: A connection object to the database.
      """
      pass
  ```

### 3.2 Inline Comments
- **Purpose**: Use inline comments to clarify complex or non-obvious code.
- **Placement**: Place comments on the line above the code they describe or at the end of the line if brief.
- **Style**: Start comments with a capital letter and leave a space after the `#`.
- **Example**:
  ```python
  # Calculate the average time per item
  avg_time_per_item = elapsed_time / processed_items
  ```

### 3.3 Blank Lines
- **Between Functions**: Use two blank lines between functions.
- **Within Functions**: Use blank lines to separate logical steps within functions.
- **Before Comments**: Leave a blank line before inline comments that introduce a new section of logic.

## 4. Error Handling

### 4.1 Try-Except Blocks
- **Use**: Use `try-except` blocks to handle errors, especially when dealing with external resources or user input.
- **Logging**: Log errors using a centralized logging function (`log_error`) for consistency.
- **Specificity**: Handle specific exceptions where possible, avoiding generic `except` clauses.

- **Example**:
  ```python
  try:
      connection = connect_to_database('data.db')
  except sqlite3.DatabaseError as e:
      log_error(e)
      raise
  ```

### 4.2 Logging Errors
- **Function Name**: Always log errors with the current function name and error message to provide context for where the error occurred.
- **Example**:
  ```python
  def log_error(e):
      print(f"Error in {inspect.currentframe().f_back.f_code.co_name}: {e}")
  ```

## 5. Code Readability

### 5.1 Line Length
- **Limit**: Keep lines of code under 80 characters where possible.
- **Breaking Long Lines**: For longer lines, break them into multiple lines for readability. Use parentheses for line continuation instead of backslashes.

- **Example**:
  ```python
  result = (
      long_function_name(parameter_one, parameter_two, parameter_three) +
      another_function_call(parameter_four)
  )
  ```

### 5.2 Indentation
- **Spacing**: Use 4 spaces per indentation level. Do not use tabs.

## 6. Function Design

### 6.1 Single Responsibility
- **Focus**: Each function should have a single, well-defined responsibility. If a function does too much, refactor it into smaller, more focused functions.

### 6.2 Parameter Handling
- **Descriptive Names**: Use clear and descriptive names for parameters.
- **Default Values**: Provide default values for optional parameters.
- **Grouping**: If a function requires many parameters, consider grouping them into a dictionary or passing an object.

### 6.3 Return Values
- **Consistency**: Every function should always return something:
  - Preferably return the main parameter.
  - Otherwise, return `True`.
  - If neither is applicable, return `None`.

## 7. Testing and Debugging

### 7.1 Testable Code
- **Isolation**: Write functions that are easy to test in isolation.
- **Avoid Side Effects**: Avoid side effects in functions; instead, return values that can be tested.

### 7.2 Debugging
- **Logging**: Use logging instead of print statements for debugging. Ensure that log messages are clear and informative.

## 8. Specific Guidelines for Code Clarity and Maintenance

### 8.1 Hard-Coded Variables
- **Placement**

: All hard-coded variables, such as XPaths, CSS selectors, string literals, and configuration values, should be defined at the beginning of each function. This makes the code easier to maintain and ensures that any changes to these variables are centralized.
  
- **Example**:
  ```python
  def submit_form(driver, wait):
      xpath_submit_button = '//*[@id="submit"]'
      success_message = "Form submitted"
      
      button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_submit_button)))
      button.click()
      print(success_message)
  ```

### 8.2 Conditional Logic
- **Regressive Conditionals**: When designing loops that require conditional operations at specific iterations, use regressive logic to ensure the condition is met towards the end of the loop.
  
- **Example**:
  ```python
  if (total_items - current_index - 1) % (batch_size * 20 * 5) == 0:
      # Perform action
  ```

### 8.3 Timing and Loops
- **Timing Initialization**: When measuring execution time within loops, always initialize the `start_time` variable immediately before the loop begins. This ensures accurate tracking of the loop's execution duration.
  
- **Example**:
  ```python
  start_time = time.time()
  for i, item in enumerate(items):
      # Loop logic
  ```

### 8.4 Function Comments and Documentation
- **Inline Comments**: Add comments to describe the purpose of logical blocks within functions, especially where operations or decisions are made. Comments should be clear and concise, explaining *why* a block of code is necessary.

- **Example**:
  ```python
  # Initialize WebDriver
  driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
  ```

### 8.5 Code Structure
- **Consistent Naming**: Ensure that variables, functions, and classes follow a consistent naming convention that reflects their purpose. Use descriptive names to enhance readability.

- **Example**:
  ```python
  total_pages = max(pages) - 1  # Calculate the total number of pages to iterate over
  ```
