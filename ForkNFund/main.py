import sqlite3
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
import json
import os

# Initialize the SQLite database
class ForkNFund(App):
    def on_start(self):
        # Create or connect to SQLite database
        self.conn = sqlite3.connect("budget_data.db")
        self.cursor = self.conn.cursor()

        # Create a table if it doesn't exist
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weekly_budget INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0
        )
        """)
        self.conn.commit()

        # Ensure there's always one row of data
        self.cursor.execute("SELECT * FROM budget")
        if not self.cursor.fetchone():
            self.cursor.execute("INSERT INTO budget (weekly_budget, total_spent) VALUES (0, 0)")
            self.conn.commit()

    def on_stop(self):
        # Close the database connection when the app stops
        self.conn.close()

class MainPage(Screen):
    def budget(self):
        # Navigate to the budget tracker page
        self.manager.current = "budget"

    def get_budget_data(self):
        app = App.get_running_app()
        cursor = app.cursor

        cursor.execute("SELECT weekly_budget, total_spent FROM budget")
        data = cursor.fetchone()
        if data:
            return data
        return (0, 0)

    def update_labels(self):
        weekly_budget, total_spent = self.get_budget_data()
        self.ids.current_budget.text = f"P{weekly_budget-total_spent}"

        self.conn = sqlite3.connect("inventory.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("SELECT * FROM inventory WHERE quantity = 0")
        out_of_stock = self.cursor.fetchall()

        # Clear the existing widgets in the grid layout
        self.ids.items_grid.clear_widgets()

        # Add each row from the inventory
        for item, quantity in out_of_stock:
            self.ids.items_grid.add_widget(Label(text=item, size_hint_x=0.5))

class BudgetManager(Screen):
    def get_budget_data(self):
        app = App.get_running_app()
        cursor = app.cursor

        cursor.execute("SELECT weekly_budget, total_spent FROM budget")
        data = cursor.fetchone()
        if data:
            return data
        return (0, 0)

    def update_labels(self):
        weekly_budget, total_spent = self.get_budget_data()
        self.ids.text_budget.text = f"P{weekly_budget}"
        self.ids.text_spent.text = f"P{total_spent}"
        self.ids.set_budget.text = ""
        self.ids.subtract_budget.text = ""

    def set_budget(self):
        app = App.get_running_app()
        cursor = app.cursor
        conn = app.conn

        try:
            new_budget = int(self.ids.set_budget.text)
            cursor.execute("UPDATE budget SET weekly_budget = ?", (new_budget,))
            conn.commit()

            # Update the labels
            self.update_labels()
        except ValueError:
            print("Invalid input for budget. Please enter a number.")

    def subtract_budget(self):
        app = App.get_running_app()
        cursor = app.cursor
        conn = app.conn

        try:
            spent = int(self.ids.subtract_budget.text)
            cursor.execute("SELECT total_spent, weekly_budget FROM budget")
            total_spent, weekly_budget = cursor.fetchone()

            if spent <= weekly_budget - total_spent:
                total_spent += spent
                cursor.execute("UPDATE budget SET total_spent = ?", (total_spent,))
                conn.commit()

                # Update the labels
                self.update_labels()
            else:
                print("Insufficient budget!")
        except ValueError:
            print("Invalid input for spent amount. Please enter a number.")

    def update_labels(self):
        weekly_budget, total_spent = self.get_budget_data()
        self.ids.text_budget.text = f"P{weekly_budget}"
        self.ids.text_spent.text = f"P{total_spent}"
        self.ids.set_budget.text = ""
        self.ids.subtract_budget.text = ""

    def on_enter(self):
        # Refresh the labels when the screen is loaded
        self.update_labels()

    def reset_values(self):
        app = App.get_running_app()
        cursor = app.cursor
        conn = app.conn

        # Reset the values of budget and expense
        cursor.execute("UPDATE budget SET total_spent = 0")
        conn.commit()
        cursor.execute("UPDATE budget SET weekly_budget = 0")
        conn.commit()
        self.update_labels()

class Inventory(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_connect()

    def db_connect(self):
        # Connect to SQLite database
        self.conn = sqlite3.connect("inventory.db")
        self.cursor = self.conn.cursor()
        # Create table if not exists
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                item TEXT NOT NULL PRIMARY KEY,
                quantity INTEGER NOT NULL
            )
        """)
        self.conn.commit()

    def add_item(self):
        self.conn = sqlite3.connect("inventory.db")
        self.cursor = self.conn.cursor()
        # Get item and quantity from input
        item = (self.ids.item.text).title()
        quantity = self.ids.quantity.text
        try:
            if item and quantity.isdigit():
                self.cursor.execute("INSERT INTO inventory (item, quantity) VALUES (?, ?)", (item, int(quantity)))
                self.conn.commit()
                self.ids.item.text = ""  # Clear input
                self.ids.quantity.text = ""
                print("Item added!")
            else:
                print("Invalid input!")
        except sqlite3.Error:
            print("Item already exists in inventory")

        self.get_inventory()

    def update_item(self):
        self.conn = sqlite3.connect("inventory.db")
        self.cursor = self.conn.cursor()
        item = (self.ids.item.text).title()
        quantity = self.ids.quantity.text
        if quantity.isdigit():
            self.cursor.execute("UPDATE inventory SET quantity = ? WHERE item = ?", (int(quantity), item))
            self.conn.commit()
            print(f"Updated {item} with quantity {quantity}")
            self.ids.item.text = ""  # Clear input
            self.ids.quantity.text = ""
        else:
            print("Invalid quantity!")

        self.get_inventory()

    def delete_item(self):
        self.conn = sqlite3.connect("inventory.db")
        self.cursor = self.conn.cursor()
        # Get item and quantity from input
        item = (self.ids.item.text).title()
        self.cursor.execute("DELETE FROM inventory WHERE item = ?", (item,))
        self.conn.commit()
        print(f"Deleted {item}")
        self.ids.item.text = ""  # Clear input
        self.ids.quantity.text = ""

        self.get_inventory()

    def get_inventory(self):
        self.conn = sqlite3.connect("inventory.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("SELECT * FROM inventory")
        inventory = self.cursor.fetchall()

        # Clear the existing widgets in the grid layout
        self.ids.items_grid.clear_widgets()

        # Add header row
        self.ids.items_grid.add_widget(Label(text="Item", bold=True, size_hint_x=0.5))
        self.ids.items_grid.add_widget(Label(text="Quantity", bold=True, size_hint_x=0.5))

        # Add each row from the inventory
        for item, quantity in inventory:
            self.ids.items_grid.add_widget(Label(text=item, size_hint_x=0.5))
            self.ids.items_grid.add_widget(Label(text=str(quantity), size_hint_x=0.5))

    def clear_inventory(self):
        self.conn = sqlite3.connect("inventory.db")
        self.cursor = self.conn.cursor()

        # Deletes all rows in the inventory table
        self.cursor.execute("DELETE FROM inventory")
        self.conn.commit()
        self.ids.items_grid.clear_widgets()
        print("Database cleared!")

    def on_leave(self):
        # Close connection when leaving the screen
        self.conn.close()

class Grocery(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_connect()

    def db_connect(self):
        # Connect to SQLite database
        self.conn = sqlite3.connect("grocery.db")
        self.cursor = self.conn.cursor()
        # Create table if not exists
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS grocery (
                item TEXT NOT NULL PRIMARY KEY,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        """)
        self.conn.commit()

    def add_to_cart(self):
        self.conn = sqlite3.connect("grocery.db")
        self.cursor = self.conn.cursor()
        # Get item and quantity from input
        cart = (self.ids.cart.text).title()
        quantity = self.ids.quantity.text
        price = self.ids.price.text
        try:
            if cart and quantity.isdigit() and price.isdigit():
                self.cursor.execute("INSERT INTO grocery (item, quantity, price) VALUES (?, ?, ?)",
                                    (cart, int(quantity), float(price)))
                self.conn.commit()
                self.ids.cart.text = ""  # Clear input
                self.ids.quantity.text = ""
                self.ids.price.text = ""
                print("Item added!")
            else:
                print("Invalid input!")
        except sqlite3.Error:
            print("Item already exists in inventory")

        self.get_cart()

    def update_cart(self):
        self.conn = sqlite3.connect("grocery.db")
        self.cursor = self.conn.cursor()
        cart = (self.ids.cart.text).title()
        quantity = self.ids.quantity.text
        price = self.ids.price.text
        if quantity:
            if quantity.isdigit():
                self.cursor.execute("UPDATE grocery SET quantity = ? WHERE item = ?", (int(quantity), cart))
                self.conn.commit()
            else:
                print("Invalid quantity!")
        if price:
            self.cursor.execute("UPDATE grocery SET price = ? WHERE item = ?", (float(price), cart))
            self.conn.commit()
        self.ids.cart.text = ""  # Clear input
        self.ids.quantity.text = ""
        self.ids.price.text = ""
        print(f"Updated {cart} with quantity {quantity} and price {price}")

        self.get_cart()

    def delete_from_cart(self):
        self.conn = sqlite3.connect("grocery.db")
        self.cursor = self.conn.cursor()
        cart = (self.ids.cart.text).title()
        self.cursor.execute("DELETE FROM grocery WHERE item = ?", (cart,))
        self.conn.commit()
        self.ids.cart.text = ""  # Clear input
        self.ids.quantity.text = ""
        self.ids.price.text = ""
        print(f"Deleted {cart}")

        self.get_cart()

    def get_cart(self):
        self.conn = sqlite3.connect("grocery.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("SELECT * FROM grocery")
        grocery = self.cursor.fetchall()

        self.ids.items_grid.clear_widgets()

        self.ids.items_grid.add_widget(Label(text="Item", bold=True, size_hint_x=0.5))
        self.ids.items_grid.add_widget(Label(text="Quantity", bold=True, size_hint_x=0.5))
        self.ids.items_grid.add_widget(Label(text="Price(PHP)", bold=True, size_hint_x=0.5))

        for item, quantity, price in grocery:
            self.ids.items_grid.add_widget(Label(text=item, size_hint_x=0.5))
            self.ids.items_grid.add_widget(Label(text=str(quantity), size_hint_x=0.5))
            self.ids.items_grid.add_widget(Label(text=str(price), size_hint_x=0.5))

    def clear_cart(self):
        self.conn = sqlite3.connect("grocery.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("DELETE FROM grocery")
        self.conn.commit()
        self.ids.items_grid.clear_widgets()
        print("Database cleared!")

    def checkout(self):
        # Connect to grocery database
        grocery_conn = sqlite3.connect("grocery.db")
        grocery_cursor = grocery_conn.cursor()

        # Connect to inventory database
        inventory_conn = sqlite3.connect("inventory.db")
        inventory_cursor = inventory_conn.cursor()

        # Connect to budget_data database
        budget_conn = sqlite3.connect("budget_data.db")
        budget_cursor = budget_conn.cursor()

        grocery_cursor.execute("SELECT * FROM grocery")
        grocery_items = grocery_cursor.fetchall()

        total_spent = 0  # Initialize total spent

        for item, quantity, price in grocery_items:
            # Calculate total price for each item
            total_spent += quantity * price

            # Check if item exists in inventory
            inventory_cursor.execute("SELECT quantity FROM inventory WHERE item = ?", (item,))
            result = inventory_cursor.fetchone()

            if result:
                # Update inventory quantity
                updated_quantity = result[0] + quantity
                inventory_cursor.execute("UPDATE inventory SET quantity = ? WHERE item = ?", (updated_quantity, item))
            else:
                # If item does not exist, add it to inventory
                inventory_cursor.execute("INSERT INTO inventory (item, quantity) VALUES (?, ?)", (item, quantity))

        inventory_conn.commit()

        # Update total_spent in budget_data
        budget_cursor.execute("SELECT total_spent FROM budget")
        current_spent = budget_cursor.fetchone()[0]
        new_total = current_spent + total_spent

        budget_cursor.execute("UPDATE budget SET total_spent = ?", (new_total,))
        budget_conn.commit()

        print(f"Checkout complete! Total spent: PHP {total_spent}")

        # Clear grocery database
        grocery_cursor.execute("DELETE FROM grocery")
        grocery_conn.commit()
        self.ids.items_grid.clear_widgets()

        # Close connections
        inventory_conn.close()
        budget_conn.close()

class Meals(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_connect()

    def db_connect(self):
        # Connect to SQLite database
        self.conn = sqlite3.connect("recipes.db")
        self.cursor = self.conn.cursor()
        # Create table if not exists
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe (
                recipe TEXT NOT NULL PRIMARY KEY,
                ingredients TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def add_to_recipes(self):
        self.conn = sqlite3.connect("recipes.db")
        self.cursor = self.conn.cursor()
        # Get item and quantity from input
        recipe = (self.ids.recipe_name.text).title()
        ingredients = (self.ids.ingredients.text).title()
        try:
            self.cursor.execute("INSERT INTO recipe (recipe, ingredients) VALUES (?, ?)",
                                (recipe, ingredients))
            self.conn.commit()
            self.ids.recipe_name.text = ""
            self.ids.ingredients.text = ""
            self.ids.ingredients_grid.clear_widgets()
            self.ids.ingredients_grid.add_widget(Label(text=str(f"{recipe} added"), size_hint_x=0.5))
            print("Item added!")
        except sqlite3.Error:
            print("Item already exists in recipes")

    def update_recipe(self):
        self.conn = sqlite3.connect("recipes.db")
        self.cursor = self.conn.cursor()
        recipe = (self.ids.recipe_name.text).title()
        ingredients = (self.ids.ingredients.text).title()
        if recipe:
            self.cursor.execute("UPDATE recipe SET ingredients = ? WHERE recipe = ?", (ingredients, recipe))
            self.conn.commit()
            self.ids.recipe_name.text = ""  # Clear input
            self.ids.ingredients.text = ""
            self.ids.ingredients_grid.clear_widgets()
            self.ids.ingredients_grid.add_widget(Label(text=f"{recipe} edited ingredients to {ingredients}", bold=True, size_hint_x=0.5))
            print(f"Updated {recipe} with quantity {ingredients}")

    def clear_recipes(self):
        self.conn = sqlite3.connect("recipes.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("DELETE FROM recipe")
        self.conn.commit()
        self.ids.ingredients_grid.clear_widgets()
        self.ids.ingredients_grid.add_widget(Label(text="Recipes Cleared", bold=True, size_hint_x=0.5))
        print("Database cleared!")

    def get_ingredients(self):
        self.conn = sqlite3.connect("recipes.db")
        self.cursor = self.conn.cursor()

        search = (self.ids.meal_search.text).title()
        self.cursor.execute("SELECT ingredients FROM recipe WHERE recipe = ?", (search,))
        ingredients = self.cursor.fetchone()

        self.ids.ingredients_grid.clear_widgets()

        self.ids.ingredients_grid.add_widget(Label(text=str(search), size_hint_x=0.5))
        self.ids.ingredients_grid.add_widget(Label(text=str(f"Ingredients: {ingredients[0]}"), size_hint_x=0.5))

        self.ids.meal_search.text = ""

    def delete_recipe(self):
        self.conn = sqlite3.connect("recipes.db")
        self.cursor = self.conn.cursor()
        recipe = (self.ids.recipe_name.text).title()
        if recipe:
            self.cursor.execute("DELETE FROM recipe WHERE recipe = ?", (recipe,))
            self.conn.commit()
            self.ids.ingredients_grid.clear_widgets()
            self.ids.ingredients_grid.add_widget(Label(text=str(f"{recipe} deleted"), size_hint_x=0.5))
            print(f"Deleted {recipe}")
            self.ids.recipe_name.text = ""  # Clear input
            self.ids.ingredients.text = ""


if __name__ == "__main__":
    ForkNFund().run()