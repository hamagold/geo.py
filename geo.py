import webbrowser
import requests
import socket
from flask import Flask, request, jsonify
import threading
from werkzeug.serving import make_server

app = Flask(__name__)

# Global variable to store the location
shared_location = None
server = None

@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>Location Sharing</title>
        <script>
            function sharePreciseLocation() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            var lat = position.coords.latitude;
                            var lon = position.coords.longitude;
                            // Send to server
                            fetch('/store_location?lat=' + lat + '&lon=' + lon)
                                .then(response => window.location = "/location_shared");
                        },
                        function(error) {
                            alert("Error getting location: " + error.message);
                            window.location = "/location_error";
                        },
                        {enableHighAccuracy: true, timeout: 10000, maximumAge: 0}
                    );
                } else {
                    alert("Geolocation is not supported by this browser.");
                    window.location = "/location_error";
                }
            }
        </script>
    </head>
    <body>
        <h1>Location Sharing Request</h1>
        <p>Do you want to share your precise location?</p>
        <button onclick="sharePreciseLocation()" style="background-color: green; color: white; padding: 10px 20px; border: none; cursor: pointer;">Allow</button>
        <a href="/no" style="background-color: red; color: white; padding: 10px 20px; text-decoration: none; margin-left: 20px;">No</a>
    </body>
    </html>
    """

@app.route('/store_location')
def store_location():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        global shared_location
        shared_location = {
            'latitude': lat,
            'longitude': lon,
            'precision': 'high'
        }
        
        # Get address information using nominatim (OpenStreetMap)
        try:
            response = requests.get(f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}').json()
            shared_location['address'] = response.get('display_name', 'Unknown address')
        except:
            shared_location['address'] = 'Address lookup failed'
        
        return "Location stored"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/location_shared')
def location_shared():
    return """
    <html>
    <body>
        <h1>Location Shared</h1>
        <p>Your precise location has been shared.</p>
        <p>You can close this window.</p>
    </body>
    </html>
    """

@app.route('/location_error')
def location_error():
    return """
    <html>
    <body>
        <h1>Error</h1>
        <p>Could not get your precise location.</p>
    </body>
    </html>
    """

@app.route('/no')
def no():
    return """
    <html>
    <body>
        <h1>Request Denied</h1>
        <p>Location sharing was not allowed.</p>
    </body>
    </html>
    """

@app.route('/get_location')
def get_location():
    return jsonify(shared_location) if shared_location else jsonify({'error': 'No location shared yet'})

def start_server():
    global server
    port = 5000
    server = make_server('0.0.0.0', port, app)
    server.serve_forever()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_link():
    local_ip = get_local_ip()
    return f"http://{local_ip}:5000"

def main():
    threading.Thread(target=start_server, daemon=True).start()
    
    link = generate_link()
    print(f"Share this link with the person: {link}")
    print("Note: For precise GPS, the user must access this from a mobile device and grant location permissions.")
    
    webbrowser.open(link)
    
    try:
        while True:
            if shared_location:
                print("\nPrecise location received:")
                print(f"Coordinates: {shared_location['latitude']}, {shared_location['longitude']}")
                print(f"Address: {shared_location.get('address', 'Unknown')}")
                print(f"Google Maps link: https://www.google.com/maps?q={shared_location['latitude']},{shared_location['longitude']}")
                break
    except KeyboardInterrupt:
        print("\nShutting down server...")
        if server:
            server.shutdown()
        print("Server stopped.")

if __name__ == '__main__':
    main()
