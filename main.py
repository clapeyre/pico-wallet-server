from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from loguru import logger
import json
import os

# Configure Loguru
logger.add(
    "wallet.log",
    rotation="10 MB",  # Rotate when file reaches 10MB
    retention="1 month",  # Keep logs for 1 month
    level="INFO",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
)

# File for persistent storage
STORAGE_FILE = "wallet_data.json"

# Default values
DEFAULT_DATA = {
    "current_value": 0.0,
    "current_message": "Bienvenue sur le portefeuille de Marcel !",
    "last_updated": datetime.now().isoformat(),
    "transactions": []
}

def save_data(data):
    try:
        # Ensure all datetime objects are converted to ISO format strings
        data_to_save = data.copy()
        data_to_save["last_updated"] = data["last_updated"].isoformat() if isinstance(data["last_updated"], datetime) else data["last_updated"]
        
        if "transactions" in data_to_save:
            for transaction in data_to_save["transactions"]:
                if isinstance(transaction.get("timestamp"), datetime):
                    transaction["timestamp"] = transaction["timestamp"].isoformat()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(STORAGE_FILE) if os.path.dirname(STORAGE_FILE) else '.', exist_ok=True)
        
        # Write to a temporary file first
        temp_file = f"{STORAGE_FILE}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        # Then rename it to the actual file (atomic operation)
        os.replace(temp_file, STORAGE_FILE)
        logger.info("Data saved to storage successfully")
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        # If we fail to save, remove the temporary file if it exists
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise

def load_data():
    try:
        if os.path.exists(STORAGE_FILE):
            try:
                with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert ISO format strings back to datetime objects
                if isinstance(data.get("last_updated"), str):
                    data["last_updated"] = datetime.fromisoformat(data["last_updated"])
                
                if "transactions" in data:
                    for transaction in data["transactions"]:
                        if isinstance(transaction.get("timestamp"), str):
                            transaction["timestamp"] = datetime.fromisoformat(transaction["timestamp"])
                
                logger.info("Data loaded from storage successfully")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {STORAGE_FILE}: {e}")
                # Backup the corrupted file
                backup_file = f"{STORAGE_FILE}.corrupted"
                logger.warning(f"Creating backup of corrupted file as {backup_file}")
                os.rename(STORAGE_FILE, backup_file)
                return create_new_data_file()
            except Exception as e:
                logger.error(f"Error loading data: {e}")
                return create_new_data_file()
        else:
            logger.info("No existing data file found, creating new one")
            return create_new_data_file()
    except Exception as e:
        logger.error(f"Unexpected error in load_data: {e}")
        return DEFAULT_DATA.copy()

def create_new_data_file():
    """Create a new data file with default values"""
    new_data = DEFAULT_DATA.copy()
    try:
        save_data(new_data)
        logger.info("Created new data file with default values")
    except Exception as e:
        logger.error(f"Failed to create new data file: {e}")
    return new_data

# Initialize global variables
stored_data = load_data()
current_value = stored_data["current_value"]
current_message = stored_data["current_message"]
last_updated = stored_data["last_updated"]

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Transaction(BaseModel):
    timestamp: datetime
    value: float
    previous_value: float
    message: str

class ValueResponse(BaseModel):
    value: float
    message: str
    last_updated: datetime
    transactions: Optional[List[Transaction]] = None

class ValueUpdate(BaseModel):
    new_value: float

class MessageUpdate(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logger.info("Homepage accessed")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/value", response_model=ValueResponse)
async def get_value():
    logger.info("Value requested")
    stored_data = load_data()
    return {
        "value": current_value,
        "message": current_message,
        "last_updated": last_updated,
        "transactions": stored_data.get("transactions", [])
    }

@app.post("/value", response_model=ValueResponse)
async def set_value(value_update: ValueUpdate):
    global current_value, current_message, last_updated
    
    # Create new transaction record
    new_transaction = {
        "timestamp": datetime.now().isoformat(),
        "value": value_update.new_value,
        "previous_value": current_value,
        "message": f"Updated value to {value_update.new_value}€"
    }
    
    # Update current values
    current_value = value_update.new_value
    last_updated = datetime.now()
    
    # Load existing data
    stored_data = load_data()
    transactions = stored_data.get("transactions", [])
    transactions.append(new_transaction)
    
    # Prepare data for storage
    data_to_save = {
        "current_value": current_value,
        "current_message": current_message,
        "last_updated": last_updated.isoformat(),
        "transactions": transactions
    }
    
    # Save to persistent storage
    save_data(data_to_save)
    
    logger.info(f"Value updated to {current_value}€")
    return {
        "value": current_value,
        "message": current_message,
        "last_updated": last_updated,
        "transactions": transactions
    }

@app.post("/message", response_model=ValueResponse)
async def set_message(message_update: MessageUpdate):
    global current_message, last_updated
    
    # Create new transaction record
    new_transaction = {
        "timestamp": datetime.now().isoformat(),
        "value": current_value,
        "previous_value": current_value,
        "message": message_update.message
    }
    
    # Update current values
    current_message = message_update.message
    last_updated = datetime.now()
    
    # Load existing data
    stored_data = load_data()
    transactions = stored_data.get("transactions", [])
    transactions.append(new_transaction)
    
    # Prepare data for storage
    data_to_save = {
        "current_value": current_value,
        "current_message": current_message,
        "last_updated": last_updated.isoformat(),
        "transactions": transactions
    }
    
    # Save to persistent storage
    save_data(data_to_save)
    
    logger.info(f"Message updated to: {current_message}")
    return {
        "value": current_value,
        "message": current_message,
        "last_updated": last_updated,
        "transactions": transactions
    }

# Separate response model for transactions endpoint
class TransactionResponse(BaseModel):
    transactions: List[Transaction]

@app.get("/transactions", response_model=TransactionResponse)
async def get_transactions():
    stored_data = load_data()
    return {"transactions": stored_data.get("transactions", [])}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 