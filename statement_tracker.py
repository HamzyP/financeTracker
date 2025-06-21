import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog
import tkinter.ttk as ttk
import tkinter.font as tkFont
import csv
import os
from datetime import datetime
from collections import defaultdict
from config import settings, theme_settings, load_settings, save_settings

# Files used to persist data.
CATEGORIES_FILE = "categories.csv"  # Stores category mappings for different stores.
IGNORE_FILE = "ignore.csv"  # Stores ignored transactions (date, store).


# -------------------------------
# Helper functions for CSV I/O
# -------------------------------
def load_categories():
    '''
    What:
        - Loads store categories from a csv file into a dictionary
    How: 
        - Initialise an empty dictionary
        - If its empty or doesnt exist: return empty dict
        - If the file has data:
            - For each row in the file:
                - Extract store name and category
                - Add them to the dictionary (dictionary[store] = category).
    Returns:
        - A dictionary where keys are store names and values are their corresponding categories.
    '''
    categories = {}
    if not os.path.exists(CATEGORIES_FILE): # check if file does not exist
        return categories #return empty dict
    if os.path.getsize(CATEGORIES_FILE) == 0: # check if files exists but is empty
        return categories #return empty dict

    with open(CATEGORIES_FILE, 'r', newline='', encoding='utf-8') as csvfile: # open the file in read mode w/ UTF-8 encoding
        reader = csv.reader(csvfile) # create a csv reader object
        for row in reader: # iterate through each row
            if len(row) >= 2: # ensure the row has atleast two values: store name, category
                store, category = row[0], row[1] # extract store name and category
                categories[store] = category # store the data in the dict

    return categories

def save_categories(categories):
    '''
    What:
        - Saves store categories to a CSV file.
    How:
        - Open the file in write mode with UTF-8 encoding.
        - Create a CSV writer object.
        - Iterate over the dictionary items:
            - Write each store-category pair as a row in the file.
    Returns:
        - Nothing (writes data to a file).
    '''
    with open(CATEGORIES_FILE, 'w', newline='', encoding='utf-8') as csvfile: # Open file in write mode
        writer = csv.writer(csvfile) # Create CSV writer object
        for store, category in categories.items(): # Iterate over store-category pairs
            writer.writerow([store, category]) # Write each pair as a row 

def load_ignore_list():
    '''
    What:
        - Loads ignored transactions (date, store) from a CSV file into a list.

    How:
        - Initialize an empty list.
        - If the file exists:
            - Open it in read mode with UTF-8 encoding.
            - Create a CSV reader object.
            - Iterate through each row in the file:
                - If the row contains at least two elements (date, store):
                    - Extract and strip both values.
                    - Append them as a tuple to the ignore list.

    Returns:
        - A list of tuples, where each tuple contains (date, store).
    '''
    ignore_list = []  # Initialize an empty list

    if os.path.exists(IGNORE_FILE):  # Check if the file exists
        with open(IGNORE_FILE, "r", newline='', encoding="utf-8") as csvfile:  # Open file in read mode
            reader = csv.reader(csvfile)  # Create a CSV reader object
            
            for row in reader:  # Iterate through each row
                if len(row) >= 2:  # Ensure the row has at least two elements (date, store)
                    date = row[0].strip()  # Extract and clean the date
                    store = row[1].strip()  # Extract and clean the store name
                    
                    ignore_list.append((date, store))  # Append the tuple to the list

    return ignore_list  # Return the ignore list

def save_ignore_list(ignore_list):
    '''
    What:
        - Saves the ignored transactions (date, store) to a CSV file.

    How:
        - Open the file in write mode with UTF-8 encoding.
        - Create a CSV writer object.
        - Iterate over the ignore list:
            - Write each (date, store) pair as a row in the file.

    Returns:
        - Nothing (writes data to a file).
    '''
    with open(IGNORE_FILE, "w", newline='', encoding='utf-8') as csvfile:  # Open file in write mode
        writer = csv.writer(csvfile)  # Create CSV writer object
        for date, store in ignore_list:  # Iterate over (date, store) pairs
            writer.writerow([date, store])  # Write each pair as a row





# -------------------------------
# Ignore List Management Dialog
# -------------------------------
class IgnoreListDialog(tk.Toplevel):
    """
    What:
        - A dialog window to manage ignored transactions.
        - Displays two Treeview tables:
            1. "Available Transactions" (not ignored) with columns: Date, Store, Income, Outgoing, Category.
            2. "Current Ignore List" (ignored transactions) with the same columns.
        - Allows the user to filter transactions, sort columns, and move transactions between the lists.

    How:
        - Initializes UI components, including:
            - Search filters for time period, category, and store.
            - Treeviews for displaying available transactions and the ignore list.
            - Buttons for adding/removing transactions from the ignore list.
        - Loads the ignore list from a file (each entry is a (date, store) tuple).
        - Supports sorting by clicking column headers.
        - Uses event bindings to trigger filtering when search fields are updated.
        - Provides modal behavior (blocks interactions with the main window until closed).
    """
    def __init__(self, master):
        selected_theme_settings = theme_settings[settings.get("Theme", "Light")]
        super().__init__(master)
        self.configure(bg=selected_theme_settings["bg"])
        self.title("Manage Ignore List")
        self.geometry("1000x900")
        # Load the ignore list from file. Now each item is expected to be a (Date, Store) tuple.
        self.ignore_list = load_ignore_list()  # list of (date, store) pairs already ignored
        # All available stores data remains (if needed elsewhere)
        # self.all_available = available_stores  # list of tuples: (store, income, outgoing)
        # Store all transactions. Each is a tuple: (date, store, amount, category)
        # -------------------------------
        # Available Transactions Section
        # -------------------------------
        avail_frame = tk.Frame(self, bg=selected_theme_settings["bg"])  # creates a frame
        avail_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)  # packs the frame
        # -------------------------------
        # Three separate search fields (Time Period, Category, Store) with a Reset button
        # -------------------------------
        search_frame = tk.Frame(avail_frame, bg=selected_theme_settings["bg"]) # creates a frame for the search filters
        search_frame.pack(fill=tk.X, padx=5, pady=2) # packs the frame
        
        tk.Label(search_frame, text="Select Time Period:", bg=selected_theme_settings["bg"], fg=selected_theme_settings["fg"]).pack(side=tk.LEFT) # creates a label
        self.ignore_time_var = tk.StringVar() # creates a string variable
        self.ignore_time_cb = ttk.Combobox(search_frame, textvariable=self.ignore_time_var, state="readonly") # creates a combobox
        self.ignore_time_cb.pack(side=tk.LEFT, padx=5) # packs the combobox
        # Bind selection change to update filtering
        self.ignore_time_cb.bind("<<ComboboxSelected>>", lambda e:  (self.filter_available(), self.populate_ignore())) # binds the combobox to the filter_available function
        
        tk.Label(search_frame, text="Search Category:", bg=selected_theme_settings["bg"], fg=selected_theme_settings["fg"]).pack(side=tk.LEFT, padx=(10,0)) # creates a label
        self.ignore_search_cat_var = tk.StringVar() # creates a string variable
        # Trace changes in the category search field
        self.ignore_search_cat_var.trace("w", lambda *args: (self.filter_available(),self.populate_ignore())) # traces the changes in the category search field
        tk.Entry(search_frame, textvariable=self.ignore_search_cat_var, width=15).pack(side=tk.LEFT, padx=5) # creates an entry field for the category search
        
        tk.Label(search_frame, text="Search Store:", bg=selected_theme_settings["bg"], fg=selected_theme_settings["fg"]).pack(side=tk.LEFT, padx=(10,0))    # creates a label
        self.ignore_search_store_var = tk.StringVar() # creates a string variable
        # Trace changes in the store search field
        self.ignore_search_store_var.trace("w", lambda *args: (self.filter_available(),self.populate_ignore())) # traces the changes in the store search field
        tk.Entry(search_frame, textvariable=self.ignore_search_store_var, width=15).pack(side=tk.LEFT, padx=5) # creates an entry field for the store search
        
        self.reset_button = tk.Button(search_frame, text="Reset", command=self.reset_search,
                                       bg=selected_theme_settings["bg"], fg=selected_theme_settings["fg"]) # creates a reset button
        self.reset_button.pack(side=tk.LEFT, padx=(10)) # packs the reset button


        tk.Label(avail_frame, text="Available Transactions:", bg=selected_theme_settings["bg"], fg=selected_theme_settings["fg"]).pack(anchor="w")  # creates a label
        # -------------------------------
        # Available Transactions Treeview Section
        # -------------------------------
        avail_tree_frame = tk.Frame(avail_frame)  # creates a frame for the treeview
        avail_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)  # packs the frame
        
        # Define columns: Date, Store, Income, Outgoing, Category
        avail_cols = ("Date", "Store", "Income", "Outgoing", "Category")  
        self.avail_tree = ttk.Treeview(avail_tree_frame, columns=avail_cols, show="headings", selectmode="browse")  # creates a treeview widget
        self.avail_tree.heading("Date", text="Date", command=lambda: self.sorting(self.avail_tree, "Date", "date", False)) 
        self.avail_tree.column("Date", anchor="center", width=130)
        self.avail_tree.heading("Store", text="Store", command=lambda: self.sorting(self.avail_tree, "Store", "text", False)) 
        self.avail_tree.column("Store", anchor="center", width=130)
        self.avail_tree.heading("Income", text="Income", command=lambda: self.sorting(self.avail_tree, "Income", "number", False))
        self.avail_tree.column("Income", anchor="center", width=130)
        self.avail_tree.heading("Outgoing", text="Outgoing", command=lambda: self.sorting(self.avail_tree, "Outgoing", "number", False))
        self.avail_tree.column("Outgoing", anchor="center", width=130)
        self.avail_tree.heading("Category", text="Category", command=lambda: self.sorting(self.avail_tree, "Category", "text", False))
        self.avail_tree.column("Category", anchor="center", width=130)
        self.avail_tree.pack(side="left", fill=tk.BOTH, expand=True)  # packs the treeview widget
        avail_scroll = ttk.Scrollbar(avail_tree_frame, orient="vertical", command=self.avail_tree.yview)  # creates a scrollbar
        self.avail_tree.configure(yscrollcommand=avail_scroll.set)  # configures the treeview with the scrollbar
        avail_scroll.pack(side="right", fill="y")  # packs the scrollbar
        self.avail_sort_col = None 
        self.avail_sort_reverse = False 
        self.filter_available()  # Populate available transactions with current filtering
        
        tk.Button(avail_frame, text="Add Selected to Ignore", command=self.add_selectedd,
                   bg=selected_theme_settings["bg"], fg=selected_theme_settings["fg"]).pack(pady=5) # button to add selected transactions to the ignore list
        
        # -------------------------------
        # Current Ignore List Section
        # -------------------------------
        ignore_frame = tk.Frame(self, bg=selected_theme_settings["bg"]) # creates a frame for the ignore list
        ignore_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True) # packs the frame
        tk.Label(ignore_frame, text="Current Ignore List:", bg=selected_theme_settings["bg"], fg=selected_theme_settings["fg"]).pack(anchor="w") # creates a label for the ignore list
        
        ignore_tree_frame = tk.Frame(ignore_frame, bg=selected_theme_settings["bg"]) # creates a frame for the ignore list treeview
        ignore_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # packs the frame
        # Define columns for the ignore treeview
        ignore_cols = ("Date", "Store", "Income", "Outgoing", "Category") 
        self.ignore_tree = ttk.Treeview(ignore_tree_frame, columns=ignore_cols, show="headings", selectmode="browse") # creates a treeview widget
        self.ignore_tree.heading("Date", text="Date", command=lambda: self.sorting(self.ignore_tree, "Date", "date", False)) 
        self.ignore_tree.column("Date", anchor="center", width=130)
        self.ignore_tree.heading("Store", text="Store", command=lambda: self.sorting(self.ignore_tree, "Store", "text", False)) 
        self.ignore_tree.column("Store", anchor="center", width=130)
        self.ignore_tree.heading("Income", text="Income", command=lambda: self.sorting(self.ignore_tree, "Income", "number", False))
        self.ignore_tree.column("Income", anchor="center", width=130)
        self.ignore_tree.heading("Outgoing", text="Outgoing", command=lambda: self.sorting(self.ignore_tree, "Outgoing", "number", False))
        self.ignore_tree.column("Outgoing", anchor="center", width=130)
        self.ignore_tree.heading("Category", text="Category", command=lambda: self.sorting(self.ignore_tree, "Category", "text", False))
        self.ignore_tree.column("Category", anchor="center", width=130)
        
        self.ignore_tree.pack(side="left", fill=tk.BOTH, expand=True) # packs the treeview widget
        ignore_scroll = ttk.Scrollbar(ignore_tree_frame, orient="vertical", command=self.ignore_tree.yview) # creates a scrollbar
        self.ignore_tree.configure(yscrollcommand=ignore_scroll.set) # configures the treeview with the scrollbar
        ignore_scroll.pack(side="right", fill="y") # packs the scrollbar
        self.ignore_sort_col = None 
        self.ignore_sort_reverse = False
        self.populate_ignore()  # Populate the current ignore list
        self.populate_time_periods()  # Populate the time period combobox
        
        tk.Button(ignore_frame, text="Remove Selected", command=self.remove_selectedd, 
                  bg=selected_theme_settings["bg"], fg=selected_theme_settings["fg"]).pack(pady=5) # button to remove selected transactions from the ignore list
        tk.Button(self, text="Close", command=self.on_close, bg=selected_theme_settings["bg"], fg=selected_theme_settings["fg"]).pack(pady=10) # button to close the dialog
        self.grab_set() # Make the dialog modal
        self.protocol("WM_DELETE_WINDOW", self.on_close) # Handle window close event

    def populate_time_periods(self):
        '''
        What:
            - Populates the time period combobox with unique months and years from transactions.
        How:
            - Extract unique months from transaction dates (formatted as "YYYY-MM").
            - Extract unique years from transaction dates (formatted as "YYYY").
            - Merge both into a single sorted list.
            - Insert "Total" at the beginning for an overall filtering option.
            - Set the values in the time period combobox.
            - If periods exist:
                - Set the default selected value to "Total".
                - Trigger filtering to update available transactions.

        Returns:
            - Nothing (updates UI elements).
        '''
        months = set() #initialise an empty set to store unique months ("YYYY-MM")
        for t in transactions: #for each transaction
            transaction_date = t[0] #extract the date forom the transaction tuple
            formatted_month = transaction_date.strftime("%Y-%m") #format the date as YYYY-MM
            months.add(formatted_month) # add the formatted month to the set
        years = set() # a set cannot have duplicates
        for t in transactions: # iterate over each transaction
            transaction_date = t[0] # extract the date from the transaction tuple
            formatted_year = transaction_date.strftime("%Y") # format the year as YYYY
            years.add(formatted_year) # add the formatted year to the set
  

        periods = sorted(months.union(years)) # Combine months and years into a single sorted list of periods
        periods.insert(0, "Total") # Insert "Total" at the beginning of the list for overall filtering
        self.ignore_time_cb['values'] = periods # Set the values of the time period combobox in the ignore list dialog
        if periods: #if there are periods
            self.ignore_time_cb.current(0) # Set the default selected period to "Total"
            self.filter_available() # Trigger the filtering function to update the available transactions based on the selected period

    def filter_available(self):
        '''
            What:
                - Filters and displays available transactions based on search criteria to be shown in a treeview/table.
                - Excludes transactions that are in the ignore list.

            How:
                - Retrieve search filters from three input fields: Time Period, Category, and Store.
                - Iterate through all transactions:
                    - Extract date, store, amount, and category.
                    - Format the date as a string (YYYY-MM-DD).
                    - Determine if the amount represents income or outgoing.
                    - Skip transactions that are in the ignore list.
                    - Apply the time, category, and store filters.
                    - Add the remaining transactions to a filtered list.
                - Sort the filtered transactions if a sorting column is selected.
                - Clear the treeview and populate it with the filtered transactions.

            Returns:
                - Nothing (updates the available transactions treeview).
        '''
        # Retrieve search filters from the three separate fields
        time_filter = self.ignore_time_var.get().lower().strip() if self.ignore_time_var.get() else ""
        cat_filter = self.ignore_search_cat_var.get().lower().strip() if self.ignore_search_cat_var.get() else ""
        store_filter = self.ignore_search_store_var.get().lower().strip() if self.ignore_search_store_var.get() else ""
        filtered = []
        # Iterate through all transactions (each transaction is a tuple: (date, store, amount, category))
        # print(transactions)
        for transaction in transactions:
            date, store, amount, category = transaction
            # Convert date to string for display and filtering (format: YYYY-MM-DD)
            date_str = date.strftime("%Y-%m-%d")

            # Determine income and outgoing based on the amount (negative amounts represent outgoing)
            if amount < 0:
                income = 0.0
                outgoing = abs(amount)
            else:
                income = amount
                outgoing = 0.0
            # Skip the transaction if it is already in the ignore list (specific to this date and store)
            if (date_str, store) in self.ignore_list:
                continue
            # Apply time filter:
            # If a time period is selected and it's not "total", then the date must start with the filter text.
            if time_filter and time_filter != "total" and not date_str.startswith(time_filter):
                continue
            # Apply category filter: if provided, category must contain the filter text (case-insensitive)
            if cat_filter and cat_filter not in category.lower():
                continue
            # Apply store filter: if provided, store must contain the filter text (case-insensitive)
            if store_filter and store_filter not in store.lower():
                continue

            # Append the transaction (with formatted columns) to the filtered list
            filtered.append((date_str, store, income, outgoing, category))
        # If a sort column is specified, sort the filtered transactions accordingly
        if self.avail_sort_col:
            filtered.sort(key=lambda x: self.sort_key(x, self.avail_sort_col), reverse=self.avail_sort_reverse)

        # Now populate the treeview:
        # Clear all rows from the available treeview
        for row in self.avail_tree.get_children():
            self.avail_tree.delete(row)
        # Insert each transaction into the available treeview with formatted values
        for date_str, store, income, outgoing, category in filtered:
            self.avail_tree.insert("", tk.END, values=(date_str, store, f"£{income:.2f}", f"£{outgoing:.2f}", category))


    def reset_search(self):
        '''
        What:
            - Resets all search filters and updates the transaction lists.

        How:
            - Clear the time period, category, and store search fields.
            - Re-populate the available transactions and ignore list using the updated (reset) filters.

        Returns:
            - Nothing (updates the treeview by undoing the filters).
        '''
        # Reset all search fields to default (empty)
        self.ignore_time_var.set("")
        self.ignore_search_cat_var.set("")
        self.ignore_search_store_var.set("")
        # Re-populate both available and ignore treeviews based on reset filters
        self.filter_available()
        self.populate_ignore()

    def sort_key(self, row, col):
        '''
        What:
            - Determines the sorting key for a transaction row based on the selected column.

        How:
            - The row is a tuple: (Date, Store, Income, Outgoing, Category).
            - Based on the column name:
                - "Date" → Sort by date (row[0]).
                - "Store" → Sort by store name (converted to lowercase for case-insensitive sorting).
                - "Income" → Sort by income amount (row[2]).
                - "Outgoing" → Sort by outgoing amount (row[3]).
                - "Category" → Sort by category name (converted to lowercase for case-insensitive sorting).
            - If the column name is unrecognized, default to sorting by "Date".

        Returns:
            - The appropriate value from the row tuple to be used for sorting.
        '''
        # row is a tuple: (Date, Store, Income, Outgoing, Category)
        if col == "Date":
            return row[0]
        elif col == "Store":
            return row[1].lower()
        elif col == "Income":
            return row[2]
        elif col == "Outgoing":
            return row[3]
        elif col == "Category":
            return row[4].lower()
        return row[0]


    def add_selected(self):
        '''
        What:
            - Move transactions from transactions to ignored_transactions + self.ignored_list
        How:
            - remove it from the transactions list
            - add it to the ignore_list
            - add it to the ignored_transactions
            - refresh the available treeview
            - refresh the ignore treeview

        '''
        # Get the selected item in the available treeview
        selected = self.avail_tree.focus()
        if not selected:  # If no item is selected, do nothing
            return 
        values = self.avail_tree.item(selected, "values")  # Retrieve the values of the selected item
        if not values:  # If no values are returned, do nothing
            return
        # Extract the date (as a string) and store from the selected transaction
        date_str = values[0]
        store = values[1]
        # If this specific transaction (identified by date and store) is not already in the ignore list, add it
        if (date_str, store) not in self.ignore_list:
            self.ignore_list.append((date_str, store))
            save_ignore_list(self.ignore_list)  # Save the updated ignore list to file
            self.populate_ignore()  # Refresh the current ignore list treeview
            self.filter_available()  # Refresh the available transactions treeview
            for transaction in transactions:
                date_obj, store_name, amount, category = transaction
               
                if  date_obj.strftime("%Y-%m-%d") == date_str and store_name == store:
                    transactions.remove(transaction) #remove full tuple
                    break
    def add_selectedd(self):
        '''
        What:
            - Move transactions from transactions to ignored_transactions + self.ignored_list
        How:
            - remove it from the transactions list
            - add it to the ignore_list
            - add it to the ignored_transactions
            - refresh the available treeview
            - refresh the ignore treeview

        '''
        # get selected item
        selected = self.avail_tree.focus()
        if not selected:  
            return # do nothing
        values = self.avail_tree.item(selected, "values")  # Retrieve the values of the selected item

        # sort our data formatting and combine income +outgoing
        date_str, store, income, outgoing, category = values # expand the data
        income = income[1:] #remove the $ sign
        outgoing = outgoing[1:] #remove the $ sign
        income = float(income) #gotta make it a float instead of string
        outgoing = float(outgoing)
        amount = income+outgoing #we have amount as we would have it in both transactions lists
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        # if this specific transaction (identified by date and store) is not already in the ignore list
        if (date_str, store) not in self.ignore_list:
            self.ignore_list.append((date_str, store)) #add it to the ignore list
            save_ignore_list(self.ignore_list)  # save the updated ignore list to the csv
            for transaction in transactions:
                if transaction[:2] == (date_obj,store):
                    transactions.remove(transaction) # remove the transaction from ongoing transactions list
                    ignored_transactions.append(transaction) # add it to the ongoing ignored_transaction
                    self.populate_ignore()  # Refresh the current ignore list treeview
                    self.filter_available()  # Refresh the available transactions treeview
                    break

    def populate_ignore(self):
        """
        Populates the ignore treeview with transactions that exist in the ignore list.
        Filters transactions based on date, category, and store if specified.
        """
        ignore_data = []  # List to store filtered ignored transactions
        # Retrieve search filters from the three input fields
        
        time_filter = self.ignore_time_var.get().lower().strip() if self.ignore_time_var.get() else ""
        cat_filter = self.ignore_search_cat_var.get().lower().strip() if self.ignore_search_cat_var.get() else ""
        store_filter = self.ignore_search_store_var.get().lower().strip() if self.ignore_search_store_var.get() else ""
        for transaction in ignored_transactions:
            date, store, amount, category = transaction  # Unpack transaction details
            date_str = date.strftime("%Y-%m-%d")  # Convert date to a string format (no time)
            if (date_str, store) in self.ignore_list:

                if amount < 0:
                    income = 0.0
                    outgoing = abs(amount)
                elif amount > 0:
                    income = amount
                    outgoing = 0.0
                            # Apply time filter: Only include transactions that match the selected period
                if time_filter and time_filter != "total" and not date_str.startswith(time_filter):
                    continue  # Skip this transaction if it doesn't match the filter

                # Apply category filter: Ignore transactions that do not contain the search term
                if cat_filter and cat_filter not in category.lower():
                    continue  # Skip transactions that do not match the category filter

                # Apply store filter: Ignore transactions that do not contain the search term
                if store_filter and store_filter not in store.lower():
                    continue  # Skip transactions that do not match the store filter
            ignore_data.append((date_str, store, income, outgoing, category))

        # Refresh the ignore list to ensure it contains the latest saved transactions
        self.ignore_list = load_ignore_list()
        
        for transaction in transactions:
            date, store, amount, category = transaction  # Unpack transaction details
            date_str = date.strftime("%Y-%m-%d")  # Convert date to a string format (no time)           
            if (date_str, store) in self.ignore_list:
                # Apply time filter: Only include transactions that match the selected period
                if time_filter and not date_str.startswith(time_filter):
                    continue  # Skip this transaction if it doesn't match the filter

                # Apply category filter: Ignore transactions that do not contain the search term
                if cat_filter and cat_filter not in category.lower():
                    continue  # Skip transactions that do not match the category filter

                # Apply store filter: Ignore transactions that do not contain the search term
                if store_filter and store_filter not in store.lower():
                    continue  # Skip transactions that do not match the store filter

                # Determine if the transaction is an income or an outgoing expense
                if int(amount) < 0:
                    income = 0.0
                    outgoing = abs(amount)  # Convert negative values to positive outgoing amounts
                else:
                    income = amount
                    outgoing = 0.0

                # Store the filtered transaction for later insertion into the treeview
                ignore_data.append((date_str, store, income, outgoing, category))

        # If sorting is applied, reorder the ignore list based on the selected column
        if self.ignore_sort_col:
            ignore_data.sort(
                key=lambda x: self.sort_key(x, self.ignore_sort_col),
                reverse=self.ignore_sort_reverse
            )

        # Clear existing treeview items before inserting new data
        self.ignore_tree.delete(*self.ignore_tree.get_children())

        # Insert new ignored transactions into the treeview
        for date_str, store, income, outgoing, category in ignore_data:
            self.ignore_tree.insert(
                "", tk.END,
                values=(date_str, store, f"\u00a3{income:.2f}", f"\u00a3{outgoing:.2f}", category)
            )

        # print("Ignore tree updated successfully.")  # Debugging confirmation




    def sorting(self,tv, col, dtype, reverse):
        list = []
        for k in tv.get_children(''):
            value = tv.set(k, col)
            if dtype == "date":
                try:
                    value = datetime.strptime(value, "%d %b %Y")
                except Exception:
                    pass #if exception fails, keep as strings
            elif dtype == "number":
                try:
                    value = float(value.replace("£", "").replace(",", ""))
                except Exception:
                    pass #if exception fails, keep as strings
            else: # default to string
                value = value.lower()
            list.append((value, k))
        list.sort(key=lambda x: x[0], reverse=reverse) #sort the list
        for index, (value, k) in enumerate(list):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.sorting(tv, col, dtype, not reverse))


    def remove_selectedd(self):
        '''
        What: 
            - removes the transaction from the ignore list/ignored_transactions and adds it to the transactions list
        How:
            - remove the selected transcation from:
                    - ignore list
                    - ignored_transactions
            - add the selected transaction to:
                    - global transactions list
            - repopulate the available treeview
            - repopulate the ignore treeview
        '''
        # get the selected item:
        selected = self.ignore_tree.focus()
        if not selected:
            return # do nothing
        values = self.ignore_tree.item(selected, "values") # grab the data from the transaction
        # sort our data formatting
        date_str, store, income, outgoing, category = values #expand our data
        income = income[1:] #remove the $ sign
        outgoing = outgoing[1:] #remove the $ sign
        income = float(income) #gotta make it a float instead of string
        outgoing = float(outgoing)
        amount = income+outgoing #we have amount as we would have it in both transactions lists
        # remove from ignore_list
        if (date_str, store) in self.ignore_list:
            self.ignore_list.remove((date_str, store)) # it is stored as date, store in ignore_list

        # remove from ignored_transactions
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        for transaction in ignored_transactions: #looping through ignored_transactions 
            if transaction[:2] == (date_obj,store): # find the one we want
                ignored_transactions.remove(transaction)
                transactions.append(transaction)
                break # only wanna remove one transactione even if its duplicate
        
        #refresh the treeviews
        save_ignore_list(self.ignore_list)
        self.populate_ignore()
        self.filter_available()
        

        
    def on_close(self):
        # Save the updated ignore list (which now contains (date, store) pairs) before closing
        # save_ignore_list(self.ignore_list)
        self.destroy()


# -------------------------------
# Main Application Class
# -------------------------------
class BankStatementApp:
    def __init__(self, master):
        self.master = master
        master.title("Bank Statement Analyser")
        self.categories = load_categories()
        global transactions
        transactions = []  # Each is a tuple: (date, store, amount, category)
        global ignored_transactions
        ignored_transactions = []
        self.summary_spending = {}
        self.summary_income = {}
        self.monthly_totals_spending = {}
        self.monthly_totals_income = {}

        self.master.bind("<Return>", self.on_enter_press) #for add categories tab 


        # Create a Notebook with tabs: Summary, Analysis, Details, Correction, Categories, Settings
        self.add_tabs(master) # Create a Notebook with tabs: Summary, Analysis, Details, Correction, Categories, Settings
        load_settings()      # loads settings from the settings.csv file
        current_theme_settings = theme_settings[settings.get("Theme", "Light")]
        self.add_bottom_buttons(master,current_theme_settings) # Bottom button frame (TOPPED) (common to all tabs)
        self.load_summary_tab() # Summary Tab – Scrolled Text
        self.load_analysis_tab(current_theme_settings) # Analysis Tab – Analysis Output, Month/Year Buttons, Net Stats, and Detail Paned Window
        # self.load_details_tab() # Details Tab – Transaction Details with Sortable Columns
        self.load_correction_tab(current_theme_settings) # Correction Tab – Transaction Correction with Category Search and Update Changes button
        self.load_categories_tab() # Categories Tab – Category Management
        # self.load_store_tab() # Store Tab - view stores
        self.load_settings_tab(current_theme_settings) # Settings Tab – Font Family, Font Size, and Theme Selection
        self.load_sort_categories_tab(current_theme_settings)
        
        self.apply_saved_theme(settings["Theme"])


        # ---------------------------
        #__init__ functions (to improve readability):
        # ---------------------------


    def add_tabs(self,master):
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.summary_tab = tk.Frame(self.notebook)
        self.analysis_tab = tk.Frame(self.notebook)
        # self.details_tab = tk.Frame(self.notebook)
        self.correction_tab = tk.Frame(self.notebook)
        self.categories_tab = tk.Frame(self.notebook)
        self.settings_tab = tk.Frame(self.notebook)
        self.categories_sorting = tk.Frame(self.notebook)
        # self.stores_tab = tk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text="Summary")
        self.notebook.add(self.analysis_tab, text="Analysis")
        # self.notebook.add(self.details_tab, text="Details")
        self.notebook.add(self.correction_tab, text="Details")
        self.notebook.add(self.categories_sorting, text="Add Categories")
        # self.notebook.add(self.stores_tab, text="View Stores")
        self.notebook.add(self.categories_tab, text="View Categories")
        self.notebook.add(self.settings_tab, text="Settings")

    
    def add_bottom_buttons(self,master,current_theme_settings):
        # Bottom button frame (TOPPED) (common to all tabs)
        self.btn_frame = tk.Frame(master, bg=current_theme_settings["bg"])
        self.btn_frame.pack(pady=5)
        self.load_button = tk.Button(self.btn_frame, text="Load CSV",bg=current_theme_settings["bg"],fg=current_theme_settings["fg"], command=self.load_csv)
        self.load_button.grid(row=0, column=0, padx=5)
        self.analyze_button = tk.Button(self.btn_frame, text="Analyse Finances",bg=current_theme_settings["bg"],fg=current_theme_settings["fg"], command=self.perform_analysis, state=tk.DISABLED)
        self.analyze_button.grid(row=0, column=1, padx=5)
        self.save_button = tk.Button(self.btn_frame, text="Save Summary CSV", bg=current_theme_settings["bg"],fg=current_theme_settings["fg"],command=self.save_summary_csv, state=tk.DISABLED)
        self.save_button.grid(row=0, column=2, padx=5)
        self.ignore_button = tk.Button(self.btn_frame, text="Manage Ignore List",bg=current_theme_settings["bg"],fg=current_theme_settings["fg"], command=self.manage_ignore_list)
        self.ignore_button.grid(row=0, column=3, padx=5)
    
    def load_summary_tab(self):
        
        self.summary_text = tk.Text(self.summary_tab)
        self.summary_scroll = ttk.Scrollbar(self.summary_tab, orient="vertical", command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=self.summary_scroll.set)
        self.summary_scroll.pack(side="right", fill="y")
        self.summary_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    def load_analysis_tab(self,current_theme_settings):
        # Create a container frame for the text widget and its scrollbar
        analysis_frame = tk.Frame(self.analysis_tab)
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create the text widget with a fixed height
        self.analysis_text = tk.Text(analysis_frame, height=10)
        self.analysis_text.pack(side="left", fill=tk.X, expand=True)

        # Create the scrollbar, linking it to the text widget
        analysis_scroll = ttk.Scrollbar(analysis_frame, orient="vertical", command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=analysis_scroll.set)
        analysis_scroll.pack(side="right", fill="y")



        self.month_button_frame = tk.Frame(self.analysis_tab, bg=current_theme_settings["bg"])
        self.month_button_frame.pack(anchor="center", padx=5, pady=5)
        self.net_stats_frame = tk.Frame(self.analysis_tab, bg=current_theme_settings["bg"])
        self.net_stats_frame.pack(fill=tk.X, padx=5, pady=5)
        self.detail_paned = ttk.PanedWindow(self.analysis_tab, orient=tk.HORIZONTAL)
        self.detail_paned.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.income_detail_frame = tk.Frame(self.detail_paned, bg=current_theme_settings["bg"])
        self.spending_detail_frame = tk.Frame(self.detail_paned, bg=current_theme_settings["bg"])
        self.detail_paned.add(self.income_detail_frame, weight=1)
        self.detail_paned.add(self.spending_detail_frame, weight=1)

    # def load_details_tab(self):


    #     # In your Details tab setup, add a top frame for filters:
    #     self.top_details = tk.Frame(self.details_tab, bg=settings["bg"])
    #     self.top_details.pack(fill=tk.X, padx=5, pady=5)

    #     # "Select Time Period" label and dropdown
    #     tk.Label(self.top_details, text="Select Time Period:", bg=settings["bg"], fg=settings["fg"]).pack(side=tk.LEFT)
    #     self.details_time_var = tk.StringVar()
    #     self.details_time_cb = ttk.Combobox(self.top_details, textvariable=self.details_time_var, state="readonly")
    #     self.details_time_cb.pack(side=tk.LEFT, padx=5)
    #     # Bind a selection event; you need to implement update_details_view() as needed.
    #     self.details_time_cb.bind("<<ComboboxSelected>>", lambda e: self.populate_details_tab())

    #     # "Search Store" label and entry
    #     tk.Label(self.top_details, text="Search Store:", bg=settings["bg"], fg=settings["fg"]).pack(side=tk.LEFT, padx=(10,0))
    #     self.details_search_var = tk.StringVar()
    #     self.details_search_var.trace("w", lambda name, index, mode: self.populate_details_tab())
    #     tk.Entry(self.top_details, textvariable=self.details_search_var, width=15).pack(side=tk.LEFT, padx=5)

    #     self.details_tree = ttk.Treeview(self.details_tab, columns=("Date", "Store", "Amount"), show="headings", selectmode="browse")
    #     for col in ("Date", "Store", "Amount",):
    #         self.details_tree.heading(col, text=col)
    #         self.details_tree.column(col, anchor="center", width=100)
    #     self.details_tree.heading("Date", text="Date", command=lambda: self.treeview_sort_column(self.details_tree, "Date", "date", False))
    #     self.details_tree.heading("Store", text="Store", command=lambda: self.treeview_sort_column(self.details_tree, "Store", "text",False))
    #     self.details_tree.heading("Amount", text="Amount", command=lambda: self.treeview_sort_column(self.details_tree, "Amount", "number", False))
    #     self.details_tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    #     corr_scroll = ttk.Scrollbar(self.details_tree, orient="vertical", command=self.details_tree.yview)
    #     self.details_tree.configure(yscrollcommand=corr_scroll.set)
    #     corr_scroll.pack(side="right", fill="y")
        

    def load_correction_tab(self,current_theme_settings):
        # frame for the select time period and search category
        self.top_corr = tk.Frame(self.correction_tab, bg=current_theme_settings["bg"]) # creates the frame
        self.top_corr.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.top_corr, text="Select Time Period:", bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(side=tk.LEFT)
        self.correction_month_var = tk.StringVar()
        self.correction_month_cb = ttk.Combobox(self.top_corr, textvariable=self.correction_month_var, state="readonly")
        self.correction_month_cb.pack(side=tk.LEFT, padx=5)
        self.correction_month_cb.bind("<<ComboboxSelected>>", lambda e: self.populate_correction_tab())


        tk.Label(self.top_corr, text="Search Category:", bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(side=tk.LEFT, padx=(10,0))
        self.correction_search_cat_var = tk.StringVar()
        self.correction_search_cat_var.trace("w", lambda name, index, mode: self.populate_correction_tab())
        tk.Entry(self.top_corr, textvariable=self.correction_search_cat_var, width=15).pack(side=tk.LEFT, padx=5)

        tk.Label(self.top_corr, text="Search Store:", bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(side=tk.LEFT, padx=(10,0))
        self.correction_search_store_var = tk.StringVar()
        self.correction_search_store_var.trace("w", lambda name, index, mode: self.populate_correction_tab())
        tk.Entry(self.top_corr, textvariable=self.correction_search_store_var, width=15).pack(side=tk.LEFT, padx=5)

        self.reset_button = tk.Button(self.top_corr, text="Reset", command=self.reset_search,bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(side=tk.LEFT,padx=(10))

        # end frame

        # Create a Treeview widget for the transaction correction table.
        self.correction_tree = ttk.Treeview(self.correction_tab, columns=("Date", "Store", "Amount", "Category"), show="headings", selectmode="browse")
        self.correction_tree.heading("Date", text="Date", command=lambda: self.treeview_sort_column(self.correction_tree, "Date", "date", False))
        self.correction_tree.heading("Store", text="Store", command=lambda: self.treeview_sort_column(self.correction_tree, "Store", "text", False))
        self.correction_tree.heading("Amount", text="Amount", command=lambda: self.treeview_sort_column(self.correction_tree, "Amount", "number", False))
        self.correction_tree.heading("Category", text="Category", command=lambda: self.treeview_sort_column(self.correction_tree, "Category", "text", False))
        
        for col in ("Date", "Store", "Amount", "Category"):
            self.correction_tree.column(col, anchor="center", width=100)
        self.correction_tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        corr_scroll = ttk.Scrollbar(self.correction_tree, orient="vertical", command=self.correction_tree.yview)
        self.correction_tree.configure(yscrollcommand=corr_scroll.set)
        corr_scroll.pack(side="right", fill="y")
        self.correction_tree.bind("<Double-1>", self.correct_transaction)
        tk.Button(self.correction_tab, text="Update Category", command=self.correct_transaction).pack(pady=5)
        # end widget

    def load_categories_tab(self):
        self.categories_tree = ttk.Treeview(self.categories_tab, columns=("Category", "Count", "Total", "Total/Count"), show="headings", selectmode="browse")
        self.categories_tree.heading("Category", text="Category", command=lambda: self.treeview_sort_column(self.categories_tree, "Category", "text", False))
        self.categories_tree.heading("Count", text="Count", command=lambda: self.treeview_sort_column(self.categories_tree, "Count", "number", False))
        self.categories_tree.heading("Total", text="Net Total", command=lambda: self.treeview_sort_column(self.categories_tree, "Total", "number", False))
        self.categories_tree.heading("Total/Count", text="Total/Count", command=lambda: self.treeview_sort_column(self.categories_tree, "Total/Count", "number", False))
        self.categories_tree.column("Category", anchor="w", width=200)
        self.categories_tree.column("Count", anchor="center", width=100)
        self.categories_tree.column("Total", anchor="center", width=120)
        self.categories_tree.column("Total/Count", anchor="center", width=120)
        self.categories_tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.categories_tree.bind("<Double-1>", lambda event, period="Total": self.on_analysis_double_click(event, period))
        cat_scroll = ttk.Scrollbar(self.categories_tree, orient="vertical", command=self.categories_tree.yview)
        self.categories_tree.configure(yscrollcommand=cat_scroll.set)
        cat_scroll.pack(side="right", fill="y")

    # def load_store_tab(self):
    #     self.store_tree = ttk.Treeview(self.stores_tab, columns=("Category", "Count", "Total"), show="headings", selectmode="browse")
    #     self.store_tree.heading("Category", text="Store", command=lambda: self.sort_categories("Category"))
    #     self.store_tree.heading("Count", text="Count", command=lambda: self.sort_categories("Count"))
    #     self.store_tree.heading("Total", text="Total", command=lambda: self.sort_categories("Total"))
    #     self.store_tree.column("Category", anchor="w", width=200)
    #     self.store_tree.column("Count", anchor="center", width=100)
    #     self.store_tree.column("Total", anchor="center", width=120)
    #     self.store_tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    #     cat_scroll = ttk.Scrollbar(self.stores_tab, orient="vertical", command=self.categories_tree.yview)
    #     self.store_tree.configure(yscrollcommand=cat_scroll.set)
    #     cat_scroll.pack(side="right", fill="y")
    #     tk.Button(self.stores_tab, text="Edit Selected", command=self.edit_category).pack(pady=5)
    #     tk.Button(self.stores_tab, text="Update Changes", command=self.update_changes).pack(pady=5)

    def load_sort_categories_tab(self, current_theme_settings):
        self.null_var = "                 "
        # Create a top frame for the two headers.
        self.top_frame = tk.Frame(self.categories_sorting, bg=current_theme_settings["bg"])
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        # tk.Label(top_frame, text="Your Categories:", bg=current_theme_settings["bg"],
        #         fg=current_theme_settings["fg"]).pack(side=tk.LEFT, padx=(10,5))
        # tk.Label(top_frame, text="Suggested Categories:", bg=current_theme_settings["bg"],
        #         fg=current_theme_settings["fg"]).pack(side=tk.LEFT, padx=(10,5))
        
        # Create a frame to hold the two Treeviews side by side.
        self.tables_frame = tk.Frame(self.categories_sorting, bg=current_theme_settings["bg"])
        self.tables_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # Left Treeview: "Non Grouped Stores"
        # Create a frame to hold the treeview and its scrollbar.
        self.store_frame = tk.Frame(self.tables_frame, bg=current_theme_settings["bg"])
        self.store_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        self.sort_tree_store = ttk.Treeview(self.store_frame, columns=("Stores",), show="headings", selectmode="browse")
        self.sort_tree_store.heading("Stores", text=f"Non Grouped Stores ({len(self.sort_tree_store.get_children())})", 
                                    command=lambda: self.treeview_sort_column(self.sort_tree_store, "Stores", "text", False))
        self.sort_tree_store.column("Stores", anchor="w", width=150)
        self.sort_tree_store.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        # Add vertical scrollbar for left treeview.
        store_scroll = ttk.Scrollbar(self.store_frame, orient="vertical", command=self.sort_tree_store.yview)
        self.sort_tree_store.configure(yscrollcommand=store_scroll.set)
        store_scroll.pack(side="right", fill="y")
        
        # # Populate with unique categories from self.categories (assuming self.categories is a dict: store->category)
        # your_cats = sorted(set(self.categories.values()))
        # for cat in your_cats:
        #     self.sort_tree_store.insert("", tk.END, values=(cat,))
        
        # Right Treeview: "Your Categories"
        # Create a frame to hold the treeview and its scrollbar.
        self.cats_frame = tk.Frame(self.tables_frame, bg=current_theme_settings["bg"])
        self.cats_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        self.sort_tree_cats = ttk.Treeview(self.cats_frame, columns=("Category",), show="headings", selectmode="browse")
        self.sort_tree_cats.heading("Category", text="Your Categories", 
                                    command=lambda: self.treeview_sort_column(self.sort_tree_cats, "Category", "text", False))
        self.sort_tree_cats.column("Category", anchor="w", width=150)
        self.sort_tree_cats.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        # Add vertical scrollbar for right treeview.
        cats_scroll = ttk.Scrollbar(self.cats_frame, orient="vertical", command=self.sort_tree_cats.yview)
        self.sort_tree_cats.configure(yscrollcommand=cats_scroll.set)
        cats_scroll.pack(side="right", fill="y")
        
        # # Only show suggested categories that are not already in your categories.
        # suggested = sorted(set(DEFAULT_CATEGORIES) - set(your_cats))
        # for cat in suggested:
        #     self.sort_tree_cats.insert("", tk.END, values=(cat,))
        
        # Bind double-click to select a category (from either treeview)
        self.sort_tree_store.bind("<ButtonRelease-1>", self.on_sort_category_select)
        
        self.sort_tree_cats.bind("<ButtonRelease-1>", self.add_cat_on_click)
        
        # Bottom frame: Entry for selected category and confirm/cancel buttons.
        self.bottom_frame = tk.Frame(self.categories_sorting, bg=current_theme_settings["bg"])
        self.bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Store Label and Entry (First Row)
        tk.Label(self.bottom_frame, text="Store:", bg=current_theme_settings["bg"], fg=current_theme_settings["fg"])\
            .grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)
        self.sort_selected_var = tk.StringVar()
        self.sort_entry_selected = tk.Entry(self.bottom_frame, textvariable=self.sort_selected_var)
        self.sort_entry_selected.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.sort_entry_selected.config(state="disabled")

        
        # Selected Category Label and Entry (Second Row)
        tk.Label(self.bottom_frame, text="Category:", bg=current_theme_settings["bg"], fg=current_theme_settings["fg"])\
            .grid(row=1, column=0, sticky="w", padx=(10, 5), pady=5)
        self.category_var = tk.StringVar()
        self.category_entry = tk.Entry(self.bottom_frame, textvariable=self.category_var)
        self.category_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        # self.sort_entry_selected.bind("<Return>", self.confirm_sort_selection)
        
        # Create a sub-frame for the buttons to avoid mixing grid and pack in the same frame.
        self.buttons_frame = tk.Frame(self.bottom_frame, bg=current_theme_settings["bg"])
        self.buttons_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.buttons_frame.columnconfigure(0, weight=1)
        

        add_category_button=tk.Button(self.buttons_frame, text="Add Category", command=self.add_category,
                bg=current_theme_settings["bg"], fg=current_theme_settings["fg"])
        add_category_button.grid(row=0, column=1, sticky="e", padx=5)  # Align to the right
        # self.category_entry.bind("<Return>", lambda event: self.add_category())
        
        self.bottom_frame.columnconfigure(1, weight=1)

        self.null_label = tk.Label(self.bottom_frame, text=self.null_var, bg=current_theme_settings["bg"], fg=current_theme_settings["fg"])
        self.null_label.grid(row=2, column=1, sticky="w", padx=(10, 5), pady=5)



    def load_settings_tab(self, current_theme_settings):
        tk.Label(self.settings_tab, 
                text="Font Family:", 
                font=(settings["FontFamily"], settings["FontSize"]), 
                bg=current_theme_settings["bg"], 
                fg=current_theme_settings["fg"]
                ).pack(anchor="w", padx=10, pady=5)

        # Create a StringVar for the font family, defaulting to the value from the global 'settings'
        # (or "Arial" if not set).
        self.font_family_var = tk.StringVar(value=settings.get("FontFamily", "Arial"))

        # List of available font options.
        font_options = ["Arial", "Helvetica", "Times New Roman", "Courier New"]

        # Create a Combobox widget for selecting the font family, using the options provided.
        self.font_family_menu = ttk.Combobox(self.settings_tab, 
                                            textvariable=self.font_family_var, 
                                            values=font_options, 
                                            state="readonly")
        self.font_family_menu.pack(anchor="w", padx=10, pady=5)

        # Create a label for "Font Size" with fixed colors.
        tk.Label(self.settings_tab, 
                text="Font size:", 
                font=(settings["FontFamily"], settings["FontSize"]), 
                bg=current_theme_settings["bg"], 
                fg=current_theme_settings["fg"]
                ).pack(anchor="w", padx=10, pady=5)

        # Create an IntVar for the font size, defaulting to the integer value from the global 'settings'
        # (or 10 if not set). The int() conversion ensures the value is an integer.
        self.font_size_var = tk.IntVar(value=int(settings.get("FontSize", "10")))

        # Create a Spinbox widget to let the user select a font size from 8 to 72.
        self.font_size_spin = tk.Spinbox(self.settings_tab, from_=8, to=72, textvariable=self.font_size_var)
        self.font_size_spin.pack(anchor="w", padx=10, pady=5)

        # Create a label for "Theme" with fixed colors.
        tk.Label(self.settings_tab, 
                text="Theme:", 
                font=("Arial", 12), 
                bg=current_theme_settings["bg"], 
                fg=current_theme_settings["fg"]
                ).pack(anchor="w", padx=10, pady=5)

        # Create a StringVar for the theme selection, defaulting to the value from the global 'settings'
        # (or "Light" if not set).
        self.theme_var = tk.StringVar(value=settings.get("Theme", "Light"),)

        # Define available theme options.
        theme_options = ["Light", "Dark"]

        # Create a Combobox widget for selecting the theme, using the options provided.

        self.theme_menu = ttk.Combobox(self.settings_tab, 
                                    textvariable=self.theme_var, 
                                    values=theme_options, 
                                    state="readonly")
        self.theme_menu.pack(anchor="w", padx=10, pady=5)

        
        # Create a button to apply settings. When clicked, it will call the apply_settings method.
        tk.Button(self.settings_tab, 
                text="Apply Settings", 
                command=self.apply_settings
                ).pack(padx=10, pady=10)
    def reset_search(self):
        self.correction_search_cat_var.set("")
        self.correction_search_store_var.set("")
        self.correction_month_var.set("Total")
        self.populate_correction_tab()


        # ---------------------------
        # Saved Theme Application
        # ---------------------------
    def apply_saved_theme(self, current_theme):
        # Retrieve the theme settings for the current theme.
        current_theme_settings = theme_settings[current_theme]

        # ---------------------------
        # Update Default Font
        # ---------------------------
        # Get the new font family and size from the settings tab widgets.
        new_font = settings["FontFamily"]
        new_size = settings["FontSize"]

        # Update the default Tkinter font with the new values.
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(family=new_font, size=new_size)
        self.master.option_add("*Font", default_font)

        # ---------------------------
        # Configure ttk Styles
        # ---------------------------
        style = ttk.Style()
        style.theme_use("default")

        # Configure Treeview style using the current theme's background and foreground. FOR THE TABLES IN OUR APP.
        style.configure("Treeview",
                        background=current_theme_settings["bg"],
                        foreground=current_theme_settings["fg"],
                        fieldbackground=current_theme_settings["bg"])
        style.configure("Treeview.Heading",
                        background=current_theme_settings["bg"],
                        foreground=current_theme_settings["fg"])
        style.map("Treeview.Heading",
          background=[("active", current_theme_settings["fg"])],
          foreground=[("active", current_theme_settings["bg"])])
        
        # Configure Notebook style using the current theme's background and foreground.
        style.configure("Custom.TNotebook", background=current_theme_settings["bg"])
        style.configure("Custom.TNotebook.Tab", 
                        background=current_theme_settings["bg"], 
                        foreground=current_theme_settings["fg"])
        style.map("Custom.TNotebook.Tab",
          background=[("selected", current_theme_settings.get("fg", current_theme_settings["bg"]))],
          foreground=[("selected", current_theme_settings.get("bg", current_theme_settings["fg"]))])

        self.notebook.configure(style="Custom.TNotebook")

        # Configure Button style with active mapping.
        style.configure("TButton", 
                        background=current_theme_settings["button_bg"], 
                        foreground=current_theme_settings["button_fg"])
        style.map("TButton",
                background=[("active", current_theme_settings["button_bg"])],
                foreground=[("active", current_theme_settings["button_fg"])])
        

        # ---------------------------
        # Update Backgrounds for Main Frames and Widgets
        # ---------------------------
        for frame in (self.summary_tab, self.analysis_tab,
                    self.correction_tab, self.categories_tab, self.settings_tab, self.categories_sorting):
            frame.configure(bg=current_theme_settings["bg"])
            for widget in frame.winfo_children():
                try:
                    widget.configure(bg=current_theme_settings["bg"], 
                                    fg=current_theme_settings["fg"])
                except Exception:
                    # If a widget doesn't support these options, simply skip it.
                    pass

        # Update the main window's background.
        self.master.configure(bg=current_theme_settings["bg"])
        
        # ---------------------------
        # Update ScrolledText Widgets
        # ---------------------------
        # Here, we're enforcing a fixed appearance for scrolled text widgets.
        self.summary_text.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"], insertbackground=current_theme_settings["fg"])
        self.analysis_text.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"], insertbackground=current_theme_settings["fg"])
        # self.details_frame.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"], insertbackground=current_theme_settings["fg"])

    # ---------------------------
    # Apply Settings Method (for Settings Tab)
    # ---------------------------
    def apply_settings(self):
        current_theme_settings = theme_settings[self.theme_var.get()]
        # Get the new font and theme settings from the settings tab widgets.
        new_font = self.font_family_var.get()
        new_size = self.font_size_var.get()
        selected_theme = self.theme_var.get()

        # Update the default Tkinter font with the new values.
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(family=new_font, size=new_size)
        self.master.option_add("*Font", default_font)


        # Get the chosen theme's settings. Defaults to "Light" if the key is not found.
        settings_dict = theme_settings.get(selected_theme, theme_settings["Light"])

        # IMPORTANT: Update the global settings dictionary with the new theme colors.
        # This ensures that any later calls (like apply_saved_theme) use the updated colors.
        # settings.update(settings_dict)
        
        # For the monthly buttons colors after you update changes.
        for widget in self.month_button_frame.winfo_children():
            # Check if the widget is a Button (assuming you're using tk.Button)
            if isinstance(widget, tk.Button):
                widget.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"])
        
        for widget in self.net_stats_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"])
        for widget in self.income_detail_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"])
        for widget in self.spending_detail_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"])

            

        # Create a ttk style object to configure widget themes.
        style = ttk.Style()
        style.theme_use("default")
                # Configure Notebook style using the current theme's background and foreground.
        style.configure("Custom.TNotebook", background=current_theme_settings["bg"])
        style.configure("Custom.TNotebook.Tab", 
                        background=current_theme_settings["bg"], 
                        foreground=current_theme_settings["fg"])
        style.map("Custom.TNotebook.Tab",
          background=[("selected", current_theme_settings.get("fg", current_theme_settings["bg"]))],
          foreground=[("selected", current_theme_settings.get("bg", current_theme_settings["fg"]))])

        self.notebook.configure(style="Custom.TNotebook")
        self.notebook.configure(style="Custom.TNotebook")

        # this updates the table colors for all pages.
        style.configure("Treeview",
                background=current_theme_settings["bg"],
                foreground=current_theme_settings["fg"],
                fieldbackground=current_theme_settings["bg"])
        style.configure("Treeview.Heading",
                        background=current_theme_settings["bg"],
                        foreground=current_theme_settings["fg"])
        style.map("Treeview.Heading",
          background=[("active", current_theme_settings["fg"])],
          foreground=[("active", current_theme_settings["bg"])])
        
        # Configure button styles with the new theme settings.
        style.configure("TButton", background=settings_dict["button_bg"], foreground=settings_dict["button_fg"])
        style.map("TButton",
                background=[("active", settings_dict["button_bg"])],
                foreground=[("active", settings_dict["button_fg"])])

        # Updates the correct categories tab color.
        self.top_corr.configure(bg=current_theme_settings["bg"])
        for widget in self.top_corr.winfo_children():
            try:
                widget.configure(bg=current_theme_settings["bg"],
                                fg=current_theme_settings["fg"])
            except Exception as e:
                print(f"Could not update widget {widget}: {e}")

        
        


        # ANALYSIS TAB COLOR UPDATES
            # Update the scrolled text widget for analysis
        try:
            self.analysis_text.configure(
                bg=current_theme_settings["bg"],
                fg=current_theme_settings["fg"],
                insertbackground=current_theme_settings["fg"]
            )
        except Exception as e:
            print("Error updating analysis_text:", e)
        
        # Update the month button frame's background
        try:
            self.month_button_frame.configure(bg=current_theme_settings["bg"])
        except Exception as e:
            print("Error updating month_button_frame:", e)
        
        # Update the net stats frame's background
        try:
            self.net_stats_frame.configure(bg=current_theme_settings["bg"])
        except Exception as e:
            print("Error updating net_stats_frame:", e)
        
        # Update the income and spending detail frames in the paned window
        try:
            self.income_detail_frame.configure(bg=current_theme_settings["bg"])
        except Exception as e:
            print("Error updating income_detail_frame:", e)
        
        try:
            self.spending_detail_frame.configure(bg=current_theme_settings["bg"])
        except Exception as e:
            print("Error updating spending_detail_frame:", e)


        # Update the background of all the main frames and their children.
        for frame in (self.summary_tab, self.analysis_tab,
                    self.correction_tab, self.categories_tab, self.settings_tab):
            frame.configure(bg=settings_dict["bg"])
            for widget in frame.winfo_children():
                try:
                    widget.configure(bg=settings_dict["bg"], fg=settings_dict["fg"])
                except Exception:
                    # Again, consider logging exceptions instead of passing silently.
                    pass

        # Update the background of all the frames inside of sort_categories
        for frame in (self.categories_sorting,self.tables_frame,self.bottom_frame,self.top_frame,self.store_frame,self.cats_frame,self.buttons_frame):
            frame.configure(bg=settings_dict["bg"])
            for widget in frame.winfo_children():
                try:
                    widget.configure(bg=settings_dict["bg"], fg=settings_dict["fg"])
                except Exception:
                    # Again, consider logging exceptions instead of passing silently.
                    pass
        # updates the background of the buttons at the bottom and the button frame itself.
        self.btn_frame.configure(bg=current_theme_settings["bg"])
        for widget in self.btn_frame.winfo_children():
            try:
                widget.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"])
            except Exception as e:
                print(f"Could not update widget {widget}: {e}")

        # Update the main window background.
        self.master.configure(bg=settings_dict["bg"])

        # Configure ScrolledText widgets to use a fixed (or themed) background.
        # Here they are forced to white, black, and black for insert background.
        # If you want these to change with the theme, adjust accordingly.
        self.summary_text.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"], insertbackground=current_theme_settings["fg"])
        self.analysis_text.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"], insertbackground=current_theme_settings["fg"])
        # self.details_frame.configure(bg=current_theme_settings["bg"], fg=current_theme_settings["fg"], insertbackground=current_theme_settings["fg"])

        # Save only FontFamily, FontSize, and Theme to the settings file.
        # Note: This does not save the color settings. If you want to persist colors,
        #       include them in the current_settings dictionary.
        current_settings = {
            "FontFamily": self.font_family_var.get(),
            "FontSize": self.font_size_var.get(),
            "Theme": self.theme_var.get()
        }
        settings.update(current_settings)
        # print(settings)
        # print(current_settings)
        save_settings(settings)

        # messagebox.showinfo("Settings Applied", "Your settings have been applied.")


    # ---------------------------
    # Data Processing and Summary Methods
    # ---------------------------
    def compute_store_totals(self):
        totals = {} 
        for date, store, amount, category in transactions:
            if store not in totals: #
                totals[store] = {"income": 0.0, "outgoing": 0.0}
            if amount < 0:
                totals[store]["outgoing"] += abs(amount)
            elif amount > 0:
                totals[store]["income"] += amount
        store_list = [(store, totals[store]["income"], totals[store]["outgoing"]) for store in totals]
        store_list.sort(key=lambda x: x[2], reverse=True)
        return store_list

    def manage_ignore_list(self):
        if transactions: # If there are transactions, compute the store totals.
            available_stores = self.compute_store_totals() 
        else: # If there are no transactions, just show an empty list.
            available_stores = []

        dialog = IgnoreListDialog(self.master) # Create the dialog window.
        self.master.wait_window(dialog) # Wait for the dialog to close.
        self.refresh_all_pages()

    def load_csv(self):
        # Allow multiple file selection
        file_paths = filedialog.askopenfilenames(
            title="Select Bank Statement CSVs", 
            filetypes=[("CSV Files", "*.csv")]
        )
        if not file_paths:
            return

        # Ask user whether to append new data or replace existing transactions.
        # Yes = Append, No = Replace
        replace_data = False
        if transactions:
            replace_data = messagebox.askyesno(
                "Load CSV",
                "Would you like to replace the current data?\n(Yes = Replace, No = Add to the data)"
            ) # returns true/false
        
        # print(replace_data)
        if replace_data:
            transactions.clear()

        self.ignore_list = load_ignore_list()

        # Process each selected CSV file.
        for file_path in file_paths:
            try:
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        try:
                            date = datetime.strptime(row["Date"], "%d %b %Y")
                        except Exception as e:
                            messagebox.showerror("Date Error", 
                                f"Error parsing date '{row['Date']}' in {os.path.basename(file_path)}: {e}")
                            continue

                        description = row["Description"]
                        store = self.extract_store_name(description)

                        try:
                            amount = float(row["Value"])
                        except Exception:
                            continue
                        category = self.categories.get(store, "None")  # Simple and error-free
                        # If the store is new, prompt for a category.
                        if store not in self.categories:
                            # existing = list(set(self.categories.values()))
                            # possible_categories = list(set(existing))
                            # possible_categories.sort()
                            # dialog = CategoryDialog(self.master, store, possible_categories)
                            # self.master.wait_window(dialog)
                            # category = dialog.result if dialog.result else "Uncategorized"
                            self.categories[store] = category
                            save_categories(self.categories)
                        else:
                            category = self.categories[store]

                        if (date.strftime("%Y-%m-%d"), store) in self.ignore_list:
                            ignored_transactions.append((date, store, amount, category))
                            continue

                        # Append the transaction to the master list.
                        transactions.append((date, store, amount, category))
            except Exception as e:
                messagebox.showerror("File Error", 
                    f"Could not read file {os.path.basename(file_path)}: {e}")
                continue

        if transactions:
            self.generate_summary()
            # self.display_summary() #called this in generate summary instead
            # Update any relevant tabs or dropdowns.
            self.populate_periods("correction")
            self.populate_categories_tab()
            self.analyze_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
            self.populate_add_categories()
        else:
            messagebox.showinfo("No Transactions", "No transactions were found in the CSVs.")
    def extract_store_name(self, description): 
        '''
        What:
            - Extracts the store name from a transaction description.

        How:
            - Split the description by commas.
            - If the resulting list has at least two parts:
                - Return the second part (store name) after stripping whitespace.
            - Otherwise, return the original description after stripping whitespace.

        Returns:
            - A string representing the extracted store name.
        '''
        parts = description.split(',')  # Split description by commas
        if len(parts) >= 2:  # Check if there are at least two parts
            return parts[1].strip()  # Return the second part after stripping whitespace
        return description.strip()  # Return the original description if no store name is found
    def populate_add_categories(self):
        # null_stores = sorted([store for store, cat in self.categories.items() if cat == "None"])
        # remove anything there already (when we update a category whilst running program)
        for item in self.sort_tree_cats.get_children():
            self.sort_tree_cats.delete(item)
        for item in self.sort_tree_store.get_children():
            self.sort_tree_store.delete(item)

        null_stores = []
        our_cats = []
        for store, cat in self.categories.items():
            if cat == "None":
                null_stores.append(store)
            else:
                our_cats.append(cat)
        
        for store in null_stores:
            self.sort_tree_store.insert("", tk.END, values=(store,))
        self.update_store_heading()
        self.treeview_sort_column(self.sort_tree_store, "Stores", "text", False)

        our_cats = sorted(set(our_cats)) # remove duplicates
        # print(our_cats)
        for cat in our_cats:
            self.sort_tree_cats.insert("", tk.END, values=(cat,))
        
        self.simulate_table_click_on_row()
            
    def simulate_table_click_on_row(self, row_index=0):
        """Simulate a row click in a ttk.Treeview without relying on bbox()."""

        # Get all children (rows)
        children = self.sort_tree_store.get_children()
        
        if not children: 
            # print("No rows available in the Treeview.")
            return

        if row_index >= len(children):
            # print(f"Row {row_index} is out of range.")
            return

        # Get the item ID for the given row index
        item = children[row_index]
        # print(f"Simulating click on item: {item}")

        # Select the item programmatically
        self.sort_tree_store.selection_set(item)  # Select the row
        self.sort_tree_store.focus(item)  # Move focus to the row

        # Simulate the <<TreeviewSelect>> event
        self.sort_tree_store.event_generate("<<TreeviewSelect>>")

        # Simulate ButtonRelease-1 event at the center of the widget
        self.sort_tree_store.event_generate("<ButtonRelease-1>", x=10, y=10)
        
        # print(f"Simulated selection and click on row {row_index}.")

    def on_enter_press(self, event):
        # tab_index = self.notebook.index(self.notebook.select())  # Get active tab index
        # print(f"Enter pressed on tab index {tab_index}")

        current_tab = self.notebook.index(self.notebook.select())  # Get active tab index

        if current_tab == 3:  # Change to the tab index where "Add Category" should trigger
            print("Enter pressed")
            self.add_category()




    def update_store_heading(self):
        count = len(self.sort_tree_store.get_children())
        self.sort_tree_store.heading("Stores", text=f"Non Grouped Stores ({count})")
    def generate_summary(self):
        summary_spending = defaultdict(lambda: defaultdict(float))
        summary_income = defaultdict(lambda: defaultdict(float))
        monthly_totals_spending = defaultdict(float)
        monthly_totals_income = defaultdict(float)
        for date, store, amount, category in transactions:
            month = date.strftime("%Y-%m")
            if amount < 0:
                summary_spending[month][category] += abs(amount)
                monthly_totals_spending[month] += abs(amount)
            elif amount > 0:
                summary_income[month][category] += amount
                monthly_totals_income[month] += amount
        self.summary_spending = summary_spending
        self.summary_income = summary_income
        self.monthly_totals_spending = monthly_totals_spending
        self.monthly_totals_income = monthly_totals_income
        self.display_summary()

    def display_summary(self):
        self.summary_text.delete(1.0, tk.END)
        all_months = sorted(set(list(self.monthly_totals_income.keys()) + list(self.monthly_totals_spending.keys())))
        if not all_months:
            self.summary_text.insert(tk.END, "No summary available.\n")
            return
        for month in all_months:
            income = self.monthly_totals_income.get(month, 0)
            spending = self.monthly_totals_spending.get(month, 0)
            net = income - spending
            self.summary_text.insert(tk.END, f"--- {month} ---\n")
            self.summary_text.insert(tk.END, f"Total Income: £{income:.2f}\n")
            self.summary_text.insert(tk.END, f"Total Spending: £{spending:.2f}\n")
            self.summary_text.insert(tk.END, f"Net: £{net:.2f}\n\n")
            self.summary_text.insert(tk.END, "Income Breakdown:\n")
            for cat, amt in sorted(self.summary_income.get(month, {}).items(), key=lambda x: x[1], reverse=True):
                self.summary_text.insert(tk.END, f"  {cat}: £{amt:.2f}\n")
            self.summary_text.insert(tk.END, "\nSpending Breakdown:\n")
            for cat, amt in sorted(self.summary_spending.get(month, {}).items(), key=lambda x: x[1], reverse=True):
                self.summary_text.insert(tk.END, f"  {cat}: £{amt:.2f}\n")
            self.summary_text.insert(tk.END, "\n")

    def save_summary_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV Files", "*.csv")],
                                                 title="Save Summary as CSV")
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Month", "Type", "Category", "Amount"])
                all_months = sorted(set(list(self.monthly_totals_income.keys()) + list(self.monthly_totals_spending.keys())))
                for month in all_months:
                    for category, total in self.summary_income.get(month, {}).items():
                        writer.writerow([month, "Income", category, f"{total:.2f}"])
                    for category, total in self.summary_spending.get(month, {}).items():
                        writer.writerow([month, "Spending", category, f"{total:.2f}"])
            messagebox.showinfo("Saved", "Summary saved successfully!")
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving summary: {e}")

    def perform_analysis(self):
        self.notebook.select(self.analysis_tab)
        self.analysis_text.delete(1.0, tk.END)
        all_months = sorted(set(list(self.monthly_totals_income.keys()) + list(self.monthly_totals_spending.keys())))
        if not all_months:
            self.analysis_text.insert(tk.END, "No analysis available.\n")
            return
        income_values = [self.monthly_totals_income.get(month, 0) for month in all_months]
        spending_values = [self.monthly_totals_spending.get(month, 0) for month in all_months]
        net_values = [inc - spend for inc, spend in zip(income_values, spending_values)]
        avg_income = sum(income_values) / len(income_values) if income_values else 0
        avg_spending = sum(spending_values) / len(spending_values) if spending_values else 0
        avg_net = sum(net_values) / len(net_values) if net_values else 0
        analysis_out = "=== Financial Analysis ===\n"
        analysis_out += f"Total income: £{sum(income_values):.2f}\n"
        analysis_out += f"Average monthly income: £{avg_income:.2f}\n"
        analysis_out += f"Average monthly spending: £{avg_spending:.2f}\n"
        analysis_out += f"Average monthly net: £{avg_net:.2f}\n\n"
        analysis_out += "Monthly Trends:\n"
        prev_net = None
        for month, inc, spend, net in zip(all_months, income_values, spending_values, net_values):
            if prev_net is None:
                change_str = "(N/A)"
            else:
                change = ((net - prev_net) / prev_net * 100) if prev_net != 0 else 0
                change_str = f"({change:+.2f}% change)"
            analysis_out += f"{month}: Net £{net:.2f} {change_str}  Expenses £{spend:.2f}  Income £{inc:.2f}\n"
            prev_net = net
        self.analysis_text.insert(tk.END, analysis_out)
        self.create_month_buttons(all_months)
        self.show_total_details() # Show the total details by default so it isnt empty. and total should always exist.

    def create_month_buttons(self, months):
        current_theme_settings = theme_settings[settings["Theme"]]
        for widget in self.month_button_frame.winfo_children():
            widget.destroy()
        unique_years = sorted(set(m.split("-")[0] for m in months))
        for year in unique_years:
            self.year_btn = tk.Button(self.month_button_frame, text=year,bg=current_theme_settings["bg"],fg=current_theme_settings["fg"], command=lambda y=year: self.show_yearly_details(y))
            self.year_btn.pack(side=tk.LEFT, padx=2)
        for m in months:
            self.btn = tk.Button(self.month_button_frame,bg=current_theme_settings["bg"],fg=current_theme_settings["fg"], text=m, command=lambda month=m: self.show_month_details(month))
            self.btn.pack(side=tk.LEFT, padx=2)
        self.total_btn = tk.Button(self.month_button_frame,bg=current_theme_settings["bg"],fg=current_theme_settings["fg"], text="Total", command=self.show_total_details)
        self.total_btn.pack(side=tk.LEFT, padx=2)

    def show_month_details(self, month):
        current_theme_settings = theme_settings[settings["Theme"]]
        for widget in self.income_detail_frame.winfo_children():
            widget.destroy()
        for widget in self.spending_detail_frame.winfo_children():
            widget.destroy()
        for widget in self.net_stats_frame.winfo_children():
            widget.destroy()
        total_income = self.monthly_totals_income.get(month, 0)
        total_spending = self.monthly_totals_spending.get(month, 0)
        net_value = total_income - total_spending
        tk.Label(self.net_stats_frame,
                 text=f"Net for {month}: £{net_value:.2f}",
                 font=(settings["FontFamily"], settings["hFontSize"], "bold"),
                 bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(anchor="center", padx=5, pady=5)
        tk.Label(self.income_detail_frame,
                 text=f"{month} Income: £{total_income:.2f}",
                 font=(settings["FontFamily"], settings["hFontSize"], "bold"),
                 bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(anchor="w", padx=10, pady=5)
        income_columns = ("Category", "Amount")
        income_tree = ttk.Treeview(self.income_detail_frame, columns=income_columns, show="headings", selectmode="browse")
        income_tree.heading("Category", text="Category", command=lambda: self.treeview_sort_column(income_tree, "Category", "text", False))
        income_tree.heading("Amount", text="Amount", command=lambda: self.treeview_sort_column(income_tree, "Amount", "number", False))
        income_tree.column("Category", anchor="w", width=150)
        income_tree.column("Amount", anchor="e", width=100)
        income_data = self.summary_income.get(month, {})
        for cat, amt in sorted(income_data.items(), key=lambda x: x[1], reverse=True):
            income_tree.insert("", tk.END, values=(cat, f"£{amt:,.2f}"))
        income_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        income_tree.bind("<Double-1>", lambda event, period=month: self.on_analysis_double_click(event, period))
        tk.Label(self.spending_detail_frame,
                 text=f"{month} Spending: £{total_spending:.2f}",
                 font=(settings["FontFamily"], settings["hFontSize"], "bold"),
                 bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(anchor="w", padx=10, pady=5)
        spend_columns = ("Category", "Amount")
        spend_tree = ttk.Treeview(self.spending_detail_frame, columns=spend_columns, show="headings", selectmode="browse")
        spend_tree.heading("Category", text="Category", command=lambda: self.treeview_sort_column(spend_tree, "Category","text", False))
        spend_tree.heading("Amount", text="Amount", command=lambda: self.treeview_sort_column(spend_tree, "Amount", "number", False))
        spend_tree.column("Category", anchor="w", width=150)
        spend_tree.column("Amount", anchor="e", width=100)
        spend_data = self.summary_spending.get(month, {})
        for cat, amt in sorted(spend_data.items(), key=lambda x: x[1], reverse=True):
            spend_tree.insert("", tk.END, values=(cat, f"£{amt:,.2f}"))
        spend_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        spend_tree.bind("<Double-1>", lambda event, period=month: self.on_analysis_double_click(event, period))


    def on_analysis_double_click(self, event, period):
        # Get the selected item from the treeview (from the analysis tab)
        tree = event.widget
        selected_item = tree.focus()
        if not selected_item:
            return
        values = tree.item(selected_item, "values")
        if not values:
            return
        # Assume the first value in the row is the category
        category = values[0]
        
        # Set the Correction tab filters:
        self.correction_month_var.set(period)
        self.correction_search_cat_var.set(category)
        
        # Call the function to refresh the Correction tab based on these new filters
        self.populate_correction_tab()
        
        # Switch to the Correction tab
        self.notebook.select(self.correction_tab)

    # def on_income_double_click(self, event, period):
    #     tree = event.widget
    #     selected_item = tree.focus()
    #     if not selected_item:
    #         return
    #     values = tree.item(selected_item, "values")
    #     if not values:
    #         return
    #     cat = values[0]
    #     self.show_transaction_details(period, cat, "Income")

    # def on_spending_double_click(self, event, period):
    #     tree = event.widget
    #     selected_item = tree.focus()
    #     if not selected_item:
    #         return
    #     values = tree.item(selected_item, "values")
    #     if not values:
    #         return
    #     cat = values[0]
    #     self.show_transaction_details(period, cat, "Spending")

    # def show_transaction_details(self, period, category, type_):
    #     current_theme_settings = theme_settings[settings["Theme"]]
    #     for widget in self.details_tab.winfo_children():
    #         widget.destroy()
    #     self.header = tk.Label(self.details_tab, text=f"Details for {period} - {category} ({type_})",
    #                        font=(settings["FontFamily"], settings["hFontSize"], "bold"),
    #                        bg=current_theme_settings["bg"],fg=current_theme_settings["fg"])
    #     self.header.pack(pady=5)
    #     tree_frame = tk.Frame(self.details_tab)
    #     tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    #     cols = ("Date", "Store", "Amount")
    #     trans_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
    #     for col in cols:
    #         trans_tree.heading(col, text=col, command=lambda c=col: self.treeview_sort_column(trans_tree, c, False))
    #         trans_tree.column(col, anchor="center", width=100)
    #     trans_tree.pack(side="left", fill=tk.BOTH, expand=True)
    #     scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=trans_tree.yview)
    #     trans_tree.configure(yscrollcommand=scroll.set)
    #     scroll.pack(side="right", fill="y")
    #     filtered = []
    #     for date, store, amount, cat in self.transactions:
    #         if cat.lower() != category.lower():
    #             continue
    #         if type_ == "Income" and amount <= 0:
    #             continue
    #         if type_ == "Spending" and amount >= 0:
    #             continue
    #         if period == "Total":
    #             filtered.append((date, store, amount))
    #         elif period.isdigit() and len(period) == 4:
    #             if date.strftime("%Y") == period:
    #                 filtered.append((date, store, amount))
    #         elif date.strftime("%Y-%m") == period:
    #             filtered.append((date, store, amount))
    #     filtered.sort(key=lambda x: x[0])
    #     for t in filtered:
    #         trans_tree.insert("", tk.END, values=(t[0].strftime("%d %b %Y"), t[1], f"£{t[2]:.2f}"))
    #     self.notebook.select(self.details_tab)

    def show_yearly_details(self, year):
        current_theme_settings = theme_settings[settings["Theme"]]
        """
        Displays the income and spending breakdown for a specific year as tables,
        along with the net balance. Clicking on a row in either table opens the
        transaction details for that category.
        
        Args:
            year (str): The selected year (e.g. "2023").
        """
        # Clear previous content
        for frame in (self.income_detail_frame, self.spending_detail_frame, self.net_stats_frame):
            for widget in frame.winfo_children():
                widget.destroy()

        # Initialize dictionaries to store yearly income and spending per category.
        yearly_income = defaultdict(float)
        yearly_spending = defaultdict(float)
        
        # Aggregate income and spending for months that belong to the given year.
        for month, breakdown in self.summary_income.items():
            if month.startswith(year):
                for cat, amt in breakdown.items():
                    yearly_income[cat] += amt
        for month, breakdown in self.summary_spending.items():
            if month.startswith(year):
                for cat, amt in breakdown.items():
                    yearly_spending[cat] += amt

        # Calculate total income and spending for the year.
        total_yearly_income = sum(self.monthly_totals_income.get(m, 0) 
                                    for m in self.monthly_totals_income if m.startswith(year))
        total_yearly_spending = sum(self.monthly_totals_spending.get(m, 0)
                                    for m in self.monthly_totals_spending if m.startswith(year))
        net_yearly = total_yearly_income - total_yearly_spending

        # Display net balance (centered).
        tk.Label(self.net_stats_frame,
                 text=f"Net for {year}: £{net_yearly:.2f}",
                 font=(settings["FontFamily"], settings["hFontSize"], "bold"),
                 bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(anchor="center", padx=5, pady=5)

        # ---------------------------
        # Income Side as Table
        # ---------------------------
        tk.Label(self.income_detail_frame,
                 text=f"{year} Income: £{total_yearly_income:.2f}",
                 font=(settings["FontFamily"], settings["hFontSize"], "bold"),
                 bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(anchor="w", padx=10, pady=5)
        income_columns = ("Category", "Amount")
        income_tree = ttk.Treeview(self.income_detail_frame, columns=income_columns, show="headings", selectmode="browse")
        income_tree.heading("Category", text="Category", command=lambda: self.treeview_sort_column(income_tree, "Category", "text", False))
        income_tree.heading("Amount", text="Amount", command=lambda: self.treeview_sort_column(income_tree, "Amount", "number", False))
        income_tree.column("Category", anchor="w", width=150)
        income_tree.column("Amount", anchor="e", width=100)
        for cat, amt in sorted(yearly_income.items(), key=lambda x: x[1], reverse=True):
            income_tree.insert("", tk.END, values=(cat, f"£{amt:,.2f}"))
        income_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        income_tree.bind("<Double-1>", lambda event, period=year: self.on_analysis_double_click(event, period))

        # ---------------------------
        # Spending Side as Table
        # ---------------------------
        tk.Label(self.spending_detail_frame,
                 text=f"{year} Spending: £{total_yearly_spending:.2f}",
                 font=(settings["FontFamily"], settings["hFontSize"], "bold"),
                 bg=current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(anchor="w", padx=10, pady=5)
        spend_columns = ("Category", "Amount")
        spend_tree = ttk.Treeview(self.spending_detail_frame, columns=spend_columns, show="headings", selectmode="browse")
        spend_tree.heading("Category", text="Category", command=lambda: self.treeview_sort_column(spend_tree, "Category", "text", False))
        spend_tree.heading("Amount", text="Amount", command=lambda: self.treeview_sort_column(spend_tree, "Amount", "number", False))
        spend_tree.column("Category", anchor="w", width=150)
        spend_tree.column("Amount", anchor="e", width=100)
        for cat, amt in sorted(yearly_spending.items(), key=lambda x: x[1], reverse=True):
            spend_tree.insert("", tk.END, values=(cat, f"£{amt:,.2f}"))
        spend_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        spend_tree.bind("<Double-1>", lambda event, period=year: self.on_analysis_double_click(event, period))


    def show_total_details(self):
        current_theme_settings = theme_settings[settings["Theme"]]
        for frame in (self.income_detail_frame, self.spending_detail_frame, self.net_stats_frame):
            for widget in frame.winfo_children():
                widget.destroy()
        total_income = defaultdict(float)
        total_spending = defaultdict(float)
        for month, breakdown in self.summary_income.items():
            for cat, amt in breakdown.items():
                total_income[cat] += amt
        for month, breakdown in self.summary_spending.items():
            for cat, amt in breakdown.items():
                total_spending[cat] += amt
        overall_income = sum(self.monthly_totals_income.values())
        overall_spending = sum(self.monthly_totals_spending.values())
        net_total = overall_income - overall_spending
        tk.Label(self.net_stats_frame,
                 text=f"Total Net: £{net_total:.2f}",
                 font=(settings["FontFamily"], settings["hFontSize"], "bold"),
                 bg= current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(anchor="center", padx=5, pady=5)
        tk.Label(self.income_detail_frame,
                 text=f"Total Income: £{overall_income:.2f}",
                 font=(settings["FontFamily"], settings["hFontSize"], "bold"),
                 bg= current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(anchor="w", padx=10, pady=5)
        income_columns = ("Category", "Amount")
        income_tree = ttk.Treeview(self.income_detail_frame, columns=income_columns, show="headings", selectmode="browse")
        income_tree.heading("Category", text="Category", command=lambda: self.treeview_sort_column(income_tree, "Category", "text", False))
        income_tree.heading("Amount", text="Amount", command=lambda: self.treeview_sort_column(income_tree, "Amount", "number", False))
        income_tree.column("Category", anchor="w", width=150)
        income_tree.column("Amount", anchor="e", width=100)
        for cat, amt in sorted(total_income.items(), key=lambda x: x[1], reverse=True):
            income_tree.insert("", tk.END, values=(cat, f"£{amt:,.2f}"))
        income_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        income_tree.bind("<Double-1>", lambda event, period="Total": self.on_analysis_double_click(event, period))
        tk.Label(self.spending_detail_frame,
                 text=f"Total Spending: £{overall_spending:.2f}",
                 font=(settings["FontFamily"], settings["hFontSize"], "bold"),
                 bg= current_theme_settings["bg"],fg=current_theme_settings["fg"]).pack(anchor="w", padx=10, pady=5)
        spend_columns = ("Category", "Amount")
        spend_tree = ttk.Treeview(self.spending_detail_frame, columns=spend_columns, show="headings", selectmode="browse")
        spend_tree.heading("Category", text="Category", command=lambda: self.treeview_sort_column(spend_tree, "Category", "text", False))
        spend_tree.heading("Amount", text="Amount", command=lambda: self.treeview_sort_column(spend_tree, "Amount", "number", False))
        spend_tree.column("Category", anchor="w", width=150)
        spend_tree.column("Amount", anchor="e", width=100)
        for cat, amt in sorted(total_spending.items(), key=lambda x: x[1], reverse=True):
            spend_tree.insert("", tk.END, values=(cat, f"£{amt:,.2f}"))
        spend_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        spend_tree.bind("<Double-1>", lambda event, period="Total": self.on_analysis_double_click(event, period))



    def treeview_sort_column(self, tv, col, dtype, reverse):
        list = []
        for k in tv.get_children(''):
            value = tv.set(k, col)
            if dtype == "date":
                try:
                    value = datetime.strptime(value, "%d %b %Y")
                except Exception:
                    pass #if exception fails, keep as strings
            elif dtype == "number":
                try:
                    value = float(value.replace("£", "").replace(",", ""))
                except Exception:
                    pass #if exception fails, keep as strings
            else: # default to string
                value = value.lower()
            list.append((value, k))
        list.sort(key=lambda x: x[0], reverse=reverse) #sort the list
        for index, (value, k) in enumerate(list):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, dtype, not reverse))

    # def on_income_double_click(self, event, period):
    #     tree = event.widget
    #     selected_item = tree.focus()
    #     if not selected_item:
    #         return
    #     values = tree.item(selected_item, "values")
    #     if not values:
    #         return
    #     cat = values[0]
    #     self.show_transaction_details(period, cat, "Income")

    def on_spending_double_click(self, event, period):
        tree = event.widget
        selected_item = tree.focus()
        if not selected_item:
            return
        values = tree.item(selected_item, "values")
        if not values:
            return
        cat = values[0]
        self.show_transaction_details(period, cat, "Spending")
    
    def on_sort_category_select(self,event):
        selected_item = self.sort_tree_store.selection() 
        if selected_item:
            store_text = self.sort_tree_store.item(selected_item, "values")[0]
            self.sort_selected_var.set(store_text)

    def add_cat_on_click(self,event):
        selected_item = self.sort_tree_cats.selection() 
        # print(selected_item)
        # print("SadasD")
        if selected_item:
            category_text = self.sort_tree_cats.item(selected_item, "values")[0]
            self.category_var.set(category_text)
    
    def add_category(self):
        
        store = self.sort_selected_var.get()
        category = self.category_var.get()
        if category == "" or store == "":
            messagebox.showerror("Error", "Please select a category to add.")
        else:
            self.categories[store] = category
            save_categories(self.categories)
            self.sort_tree_store.delete(self.sort_tree_store.selection())
            self.update_store_heading()
            self.null_var = (f"Assigned {store} to {category}")
            self.null_label.config(text=self.null_var)
            self.populate_add_categories()
            self.category_var.set("")
        
    def populate_periods(self, tab):
        
        months = set(t[0].strftime("%Y-%m") for t in transactions) # adds the months
        years = set(t[0].strftime("%Y") for t in transactions) # adds the years
        periods = sorted(months.union(years)) # combines the months and years
        periods.insert(0, "Total") # adds total to the beginning of the list 
        # if tab == "details":
        #     self.details_time_cb['values'] = periods
        #     if periods:
        #         self.details_time_cb.current(0)
        #         self.populate_details_tab()
            
        if tab == "correction":
            self.correction_month_cb['values'] = periods
            if periods:
                self.correction_month_cb.current(0)
                self.populate_correction_tab()

    # def populate_correction_periods(self):
    #     months = set(t[0].strftime("%Y-%m") for t in self.transactions)
    #     years = set(t[0].strftime("%Y") for t in self.transactions)
    #     periods = sorted(months.union(years))
    #     periods.insert(0, "Total")
    #     self.correction_month_cb['values'] = periods
    #     if periods:
    #         self.correction_month_cb.current(0)
    #         self.populate_correction_tab()
    def populate_details_tab(self):
        period = self.details_time_var.get()
        store_filter = self.details_search_var.get().lower()
        
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
        for i, (date, store, amount, category) in enumerate(transactions):
            if period == "Total":
                pass
            elif len(period) == 4:
                if date.strftime("%Y") != period:
                    continue
            elif len(period) == 7:
                if date.strftime("%Y-%m") != period:
                    continue
            else:
                continue
            if store_filter and store_filter not in store.lower():
                continue
            self.details_tree.insert("", tk.END, iid=str(i), values=(date.strftime("%d %b %Y"), store, f"£{amount:.2f}", category))

    def populate_correction_tab(self):
        period = self.correction_month_var.get()
        cat_filter = self.correction_search_cat_var.get().lower()
        store_filter = self.correction_search_store_var.get().lower()
        # self.correction_tree is the treeview widget for correction tab
        for item in self.correction_tree.get_children():
            self.correction_tree.delete(item)
        for i, (date, store, amount, category) in enumerate(transactions):
            if period == "Total":
                pass
            elif len(period) == 4:
                if date.strftime("%Y") != period:
                    continue
            elif len(period) == 7:
                if date.strftime("%Y-%m") != period:
                    continue
            else:
                continue
            if cat_filter and cat_filter not in category.lower():
                continue
            if store_filter and store_filter not in store.lower():
                continue
            self.correction_tree.insert("", tk.END, iid=str(i), values=(date.strftime("%d %b %Y"), store, f"£{amount:.2f}", category))

    def correct_transaction(self, event=None):
        # Get the currently focused item in the correction tree.
        item_id = self.correction_tree.focus()
        if not item_id:
            return

        # Retrieve the row values (assuming the 4th column is the current category).
        values = self.correction_tree.item(item_id, "values")
        if not values:
            return

        current_cat = values[3]
        
        # Ask the user for a new category, pre-populated with the current category.
        new_cat = simpledialog.askstring("Correct Category",
                                        f"Enter new category for transaction on {values[0]} at {values[1]}:",
                                        initialvalue=current_cat)
        if new_cat and new_cat != current_cat:
            # Ask if the change should be applied to all transactions for the store.
            update_all = messagebox.askyesno("Apply to All", f"Do you want to update all transactions for store '{values[1]}'?")
            if update_all:
                store = values[1]
                # Update every transaction with this store.
                for i, (d, s, amt, cat) in enumerate(transactions):
                    if s == store:
                        transactions[i] = (d, s, amt, new_cat)
                self.categories[store] = new_cat
            else:
                # Here we assume that the treeview item's ID matches the index in self.transactions.
                try:
                    index = int(item_id)
                except ValueError:
                    # If conversion fails, simply exit.
                    return
                date, store, amount, _ = transactions[index]
                transactions[index] = (date, store, amount, new_cat)
            
            # Refresh the Correction tab, summary, and categories.
            self.populate_correction_tab()
            self.generate_summary()
            self.display_summary()
            self.populate_categories_tab()
            self.show_total_details() # Simulates total details button click.


    def populate_categories_tab(self):
        # print("a")
        cat_counts = defaultdict(int) #creates a dictionary with default value of 0
        cat_totals = defaultdict(float) #creates a dictionary with default value of 0.0
        # for i in transactions:
        #     print(i)
        
        for _, _, amount, cat in transactions: #iterates through the transactions
            cat_counts[cat] += 1 #adds the category to the category count
            # print(type(amount))
            cat_totals[cat] += amount #adds the amount to the category total
        for item in self.categories_tree.get_children(): #clears the treeview
            self.categories_tree.delete(item) #deletes the item
        for cat in cat_counts: #iterates through the categories
            avg = cat_totals[cat] / cat_counts[cat] if cat_counts[cat] != 0 else 0 #calculates the average
            self.categories_tree.insert("", tk.END, values=(cat, cat_counts[cat], f"£{cat_totals[cat]:.2f}", f"£{avg:.2f}")) #inserts the values into the treeview

    def sort_categories(self, col):
        items = [(self.categories_tree.set(child, col), child) for child in self.categories_tree.get_children('')]
        if col == "Count":
            items.sort(key=lambda t: int(t[0]), reverse=True)
        elif col == "Total":
            items.sort(key=lambda t: float(t[0].replace("£", "")), reverse=True)
        else:
            items.sort(key=lambda t: t[0].lower())
        for index, (val, child) in enumerate(items):
            self.categories_tree.move(child, '', index)

    def refresh_all_pages(self):
        previous_tab = self.notebook.select()  # Store the current tab ID so we can go back to it
        self.populate_categories_tab() #view_categories tab refresh
        self.generate_summary() #summary page
        self.perform_analysis() #analysis page (will simulate total button press on analysis page)
        self.populate_periods("correction") #details tab
        # self.populate_add_categories() # this wont change anyway because of how categories is read in. 
        self.notebook.select(previous_tab)  # go back to where they were

    def edit_category(self):
        selected = self.categories_tree.focus()
        if not selected:
            messagebox.showinfo("Info", "Please select a category to edit.")
            return
        values = self.categories_tree.item(selected, "values")
        if not values:
            return
        old_cat = values[0]
        new_cat = simpledialog.askstring("Edit Category", f"Rename category '{old_cat}' to:", initialvalue=old_cat)
        if new_cat and new_cat != old_cat:
            for i, (date, store, amount, cat) in enumerate(transactions):
                if cat.lower() == old_cat.lower():
                    transactions[i] = (date, store, amount, new_cat)
            for store, cat in self.categories.items():
                if cat.lower() == old_cat.lower():
                    self.categories[store] = new_cat
            messagebox.showinfo("Updated", f"Category '{old_cat}' has been renamed to '{new_cat}'.")
            self.generate_summary()
            self.display_summary()
            self.populate_categories_tab()
            self.populate_correction_periods()

    def update_changes(self):
        self.generate_summary()
        self.display_summary()
        self.populate_periods("correction")
        self.populate_categories_tab()
        save_categories(self.categories)
        messagebox.showinfo("Updated", "Changes have been applied across the app.")

if __name__ == "__main__":
    root = tk.Tk() #creates an instance of the main tkinter window
    root.minsize(800, 600)
    app = BankStatementApp(root) #creates an instance of the class
    root.mainloop() #starts the tkinter event loop
