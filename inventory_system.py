"""
Inventory Management System

A robust, class-based inventory manager with validation, logging,
file persistence, and threshold alerts.
"""

import json
import logging
import shutil
import os
from datetime import datetime
from typing import Dict, List

try:
    from tabulate import tabulate
    USE_TABULATE = True
except ImportError:
    USE_TABULATE = False


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class InventoryError(Exception):
    """Custom exception for inventory-related errors."""


class InventorySystem:
    """Encapsulates all operations for managing inventory data."""

    def __init__(self, filepath: str = "inventory.json"):
        """
        Initialize a new InventorySystem instance.

        Args:
            filepath (str): Path to the inventory JSON file.
        """
        self.filepath = filepath
        self.stock_data: Dict[str, int] = {}
        self.logs: List[str] = []
        logger.info("Inventory system initialized.")

    # -----------------------------
    # Validation helpers
    # -----------------------------
    @staticmethod
    def _validate_item(item: str) -> None:
        """Validate that item name is a non-empty string."""
        if not isinstance(item, str) or not item.strip():
            raise InventoryError("Invalid item name. Must be a non-empty string.")

    @staticmethod
    def _validate_qty(qty: int, allow_zero: bool = False) -> None:
        """Validate that quantity is a positive integer."""
        if not isinstance(qty, int) or qty < 0 or (not allow_zero and qty == 0):
            raise InventoryError("Quantity must be a positive integer.")

    # -----------------------------
    # Core operations
    # -----------------------------
    def add_item(self, item: str, qty: int) -> bool:
        """Add an item to the inventory."""
        try:
            self._validate_item(item)
            self._validate_qty(qty, allow_zero=True)
            self.stock_data[item] = self.stock_data.get(item, 0) + qty
            msg = f"{datetime.now()}: Added {qty} of {item}"
            self.logs.append(msg)
            logger.info(msg)
            return True
        except InventoryError as e:
            logger.error("Add failed: %s", e)
            return False

    def remove_item(self, item: str, qty: int) -> bool:
        """Remove an item or reduce its quantity."""
        try:
            self._validate_item(item)
            self._validate_qty(qty)
            if item not in self.stock_data:
                raise InventoryError(f"Item '{item}' not found.")
            if self.stock_data[item] < qty:
                raise InventoryError(
                    f"Not enough '{item}' in stock to remove {qty}."
                )

            self.stock_data[item] -= qty
            if self.stock_data[item] == 0:
                del self.stock_data[item]
                logger.info("Item '%s' fully removed (stock depleted).", item)
            else:
                logger.info(
                    "Removed %d of '%s'. Remaining: %d",
                    qty,
                    item,
                    self.stock_data[item],
                )
            return True
        except InventoryError as e:
            logger.warning("Remove failed: %s", e)
            return False

    def get_qty(self, item: str) -> int:
        """Return current quantity of an item."""
        return self.stock_data.get(item, 0)

    # -----------------------------
    # File operations
    # -----------------------------
    def load_data(self) -> bool:
        """Load stock data from JSON file."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.stock_data = json.load(f)
            logger.info("Loaded inventory from %s", self.filepath)
            return True
        except FileNotFoundError:
            logger.warning(
                "File %s not found. Starting with empty inventory.",
                self.filepath,
            )
            return False
        except json.JSONDecodeError as e:
            logger.error("JSON decode error in %s: %s", self.filepath, e)
            return False

    def save_data(self) -> bool:
        """Save stock data to JSON, creating a backup first."""
        try:
            if os.path.exists(self.filepath):
                shutil.copy(self.filepath, f"{self.filepath}.bak")
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.stock_data, f, indent=2)
            logger.info("Inventory saved to %s", self.filepath)
            return True
        except (IOError, OSError) as e:
            logger.error("Error saving data: %s", e)
            return False

    # -----------------------------
    # Reports
    # -----------------------------
    def print_data(self) -> None:
        """Print a table of all inventory items."""
        print("\n=== Inventory Report ===")
        if not self.stock_data:
            print("No items in inventory.")
        else:
            if USE_TABULATE:
                print(
                    tabulate(
                        self.stock_data.items(),
                        headers=["Item", "Quantity"],
                        tablefmt="grid",
                    )
                )
            else:
                for item, qty in self.stock_data.items():
                    print(f"{item:<15} -> {qty}")
        print("========================\n")

    def check_low_items(self, threshold: int = 5) -> List[str]:
        """Return list of items below threshold."""
        if not isinstance(threshold, int) or threshold < 0:
            logger.error("Invalid threshold: %s", threshold)
            return []
        low = [item for item, qty in self.stock_data.items() if qty < threshold]
        if low:
            logger.info("Low stock items: %s", ", ".join(low))
        return low

    def summary(self) -> Dict[str, int]:
        """Return a dictionary of inventory items."""
        return dict(self.stock_data)


def main() -> None:
    """Demonstrate the functionality of the InventorySystem."""
    inv = InventorySystem()
    inv.load_data()

    inv.add_item("apple", 10)
    inv.add_item("banana", 4)
    inv.remove_item("apple", 2)

    inv.print_data()

    print("Low stock items:", inv.check_low_items())
    inv.save_data()


if __name__ == "__main__":
    main()
