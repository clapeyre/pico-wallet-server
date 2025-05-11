# Value Controller Server

A simple server that allows authorized users to view and modify a floating-point value, while providing read-only access to other devices (like microcontrollers).

## Features

- Web interface for authorized users to view and modify the value
- Read-only endpoint for microcontrollers
- JWT-based authentication
- Automatic value updates every 5 seconds
- Mobile-friendly interface

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create the necessary directories:
```bash
mkdir templates static
```

3. Start the server:
```bash
python main.py
```

The server will start on `http://0.0.0.0:8000`

## Usage

### Web Interface
1. Open `http://localhost:8000` in your web browser
2. Login with the default credentials:
   - Username: `admin`
   - Password: `admin123`
3. View and modify the value through the web interface

### Microcontroller Access
To read the value from a microcontroller, make a GET request to `/value`. The response will be in JSON format:
```json
{
    "value": 0.0
}
```

## Security Notes

Before deploying to production:
1. Change the `SECRET_KEY` in `main.py`
2. Change the default admin credentials
3. Consider adding HTTPS
4. Consider adding rate limiting
5. Consider adding persistent storage

## API Endpoints

- `GET /`: Web interface
- `GET /value`: Read the current value (no authentication required)
- `POST /value`: Update the value (requires authentication)
- `POST /token`: Get authentication token 