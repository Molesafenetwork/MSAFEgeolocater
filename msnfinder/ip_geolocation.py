import requests
import folium
import geocoder
import phonenumbers
import json
import os
import webbrowser  # Import webbrowser module
import smtplib  # Import smtplib for sending emails
from email.mime.text import MIMEText  # Import MIMEText for email content

CONFIG_FILE = 'config.json'

# Carrier mapping for Australian numbers
CARRIER_DOMAINS = {
    'telstra': 'mms.telstra.com.au',
    'optus': 'optus.mms',
    'vodafone': 'vodafone.net.au',
    # Add more carriers as needed
}

def load_config():
    """Load API credentials from the configuration file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_config(config):
    """Save API credentials to the configuration file."""
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def get_ip_info(ip_address):
    """Fetch IP geolocation information."""
    try:
        response = requests.get(f'https://ipinfo.io/{ip_address}/json')
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching IP info: {e}")
        return None

def get_phone_info(phone_number, twilio_sid=None, twilio_token=None, telynx_token=None):
    """Fetch geolocation information based on phone number."""
    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        country_code = phonenumbers.region_code_for_number(parsed_number)
        
        # Twilio Lookup for Australian Numbers
        if country_code == 'AU':
            # If Twilio credentials are provided, use them
            if twilio_sid and twilio_token:
                response = requests.get(f'https://lookups.twilio.com/v1/PhoneNumbers/{phone_number}',
                                        auth=(twilio_sid, twilio_token))
                data = response.json()
                if 'error' not in data:
                    suburb = data.get('suburb', 'Suburb not found')
                    carrier = data.get('carrier', 'Carrier not found')
                    return {'country_code': country_code, 'suburb': suburb, 'carrier': carrier}
                else:
                    print(f"Error fetching data for {phone_number}: {data['error']}")
                    return None
            else:
                print("Twilio credentials not provided. Unable to fetch carrier information.")
                return None
        
        # Telynx Lookup
        elif country_code == 'AU' and telynx_token:
            response = requests.get(f'https://api.telynx.com/v1/lookup/{phone_number}',
                                    headers={'Authorization': f'Bearer {telynx_token}'})
            data = response.json()
            if 'error' not in data:
                suburb = data.get('suburb', 'Suburb not found')
                return {'country_code': country_code, 'suburb': suburb, 'carrier': data.get('carrier')}
            else:
                print(f"Error fetching data for {phone_number}: {data['error']}")
                return None
        
        # Indian Numbers
        elif country_code == 'IN':
            response = requests.get(f'https://api.numverify.com/v2/validate?access_key=your_numverify_access_key&number={phone_number}')
            data = response.json()
            if data['valid']:
                return {'country_code': country_code, 'location': data.get('location'), 'carrier': data.get('carrier')}
            else:
                print(f"Error fetching data for {phone_number}: {data['error']}")
                return None
        
        return {'country_code': country_code}  # Return country code if no specific data is found
    except phonenumbers.NumberParseException as e:
        print(f"Error parsing phone number: {e}")
        return None

def attempt_mms_lookup(phone_number):
    """Attempt to gather information about the phone number using MMS or other protocols."""
    print(f"Attempting to gather information for {phone_number} using MMS or other protocols...")
    
    # Simulate sending an MMS and gathering information
    # In a real implementation, you would replace this with actual logic
    return {
        'status': 'success',
        'info': {
            'carrier': 'Sample Carrier',
            'locality': 'Sample Locality',
            'additional_info': 'Additional information gathered via MMS.'
        }
    }

def send_mms_via_email(phone_number, carrier, subject, message):
    """Send an MMS to the specified phone number via email."""
    if carrier not in CARRIER_DOMAINS:
        print("Carrier not supported for MMS.")
        return False

    mms_address = f"{phone_number}@{CARRIER_DOMAINS[carrier]}"
    
    # Set up the email server
    try:
        smtp_server = config.get('smtp_server', 'smtp.your_email_provider.com')  # Replace with your SMTP server
        smtp_port = config.get('smtp_port', 587)  # Common SMTP port
        smtp_user = config.get('smtp_user', 'your_email@example.com')  # Your email
        smtp_password = config.get('smtp_password', 'your_email_password')  # Your email password

        # Create the email content
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = mms_address

        # Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, mms_address, msg.as_string())
        
        print(f"MMS sent to {mms_address}.")
        return True
    except Exception as e:
        print(f"Failed to send MMS: {e}")
        return False

def call_number(phone_number, caller_number, telynx_token=None, twilio_sid=None, twilio_token=None):
    """Make a call to the specified phone number using Telynx or Twilio API."""
    try:
        if telynx_token:
            response = requests.post(
                'https://api.telynx.com/v1/call',
                headers={'Authorization': f'Bearer {telynx_token}'},
                json={'to': phone_number, 'from': caller_number}
            )
        elif twilio_sid and twilio_token:
            response = requests.post(
                'https://api.twilio.com/2010-04-01/Accounts/{}/Calls.json'.format(twilio_sid),
                auth=(twilio_sid, twilio_token),
                data={'To': phone_number, 'From': caller_number}
            )
        else:
            print("No valid API credentials provided for making a call.")
            return None

        data = response.json()
        if 'error' not in data:
            print(f"Call initiated to {phone_number} from {caller_number}.")
            return data  # Return call data for further processing
        else:
            print(f"Error initiating call: {data['error']}")
            return None
    except Exception as e:
        print(f"Error making call: {e}")
        return None

def create_map(location, country_code):
    """Create a map with the given location."""
    map_location = folium.Map(location=location, zoom_start=12)
    folium.Marker(location=location).add_to(map_location)

    # Create directory for maps
    directory = 'ipmaps'
    os.makedirs(directory, exist_ok=True)

    # Determine the base filename based on country code
    base_filename = f'ipmap{country_code}'
    file_index = 1
    map_file_path = os.path.join(directory, f'{base_filename}{file_index}.html')

    # Increment the filename if it already exists
    while os.path.exists(map_file_path):
        file_index += 1
        map_file_path = os.path.join(directory, f'{base_filename}{file_index}.html')

    map_location.save(map_file_path)

    return map_file_path

def main():
    # Load existing configuration
    config = load_config()

    # Prompt for API credentials if not already set
    if 'twilio_sid' not in config:
        config['twilio_sid'] = input("Enter your Twilio Account SID: ")
    if 'twilio_token' not in config:
        config['twilio_token'] = input("Enter your Twilio Auth Token: ")
    if 'telynx_token' not in config:
        config['telynx_token'] = input("Enter your Telynx API Token: ")

    # Prompt for SMTP configuration
    if 'smtp_server' not in config:
        config['smtp_server'] = input("Enter your SMTP server (e.g., smtp.your_email_provider.com): ")
    if 'smtp_port' not in config:
        config['smtp_port'] = input("Enter your SMTP port (e.g., 587): ")
    if 'smtp_user' not in config:
        config['smtp_user'] = input("Enter your email address: ")
    if 'smtp_password' not in config:
        config['smtp_password'] = input("Enter your email password (or app-specific password for iCloud): ")

    # Prompt for caller numbers
    if 'twilio_number' not in config:
        config['twilio_number'] = input("Enter your Twilio number to call from: ")
    if 'telynx_number' not in config:
        config['telynx_number'] = input("Enter your Telynx number to call from: ")

    # Save the configuration
    save_config(config)

    print("\nYou can change your details in the new config.json file.")

    ip_address = input("Enter an IP address (or leave blank for your own IP): ")
    if not ip_address:
        ip_address = requests.get('https://api.ipify.org').text  # Get public IP

    ip_info = get_ip_info(ip_address)
    if ip_info:
        print(f"IP Address: {ip_info.get('ip')}")
        print(f"Location: {ip_info.get('city')}, {ip_info.get('region')}, {ip_info.get('country')}")
        print(f"Coordinates: {ip_info.get('loc')}")

        # Split coordinates into latitude and longitude
        if 'loc' in ip_info:
            lat, lon = map(float, ip_info['loc'].split(','))
            # Create and save the map
            map_file_path = create_map([lat, lon], ip_info.get('country'))
            print(f"Map has been created and saved as '{map_file_path}'.")

            # Provide a clickable link to the map
            print(f"You can view the map here: file://{os.path.abspath(map_file_path)}")

    # Phone number geolocation
    phone_number = input("Enter a phone number (e.g., +14155552671): ")

    # Attempt to gather information using MMS or other protocols
    mms_info = attempt_mms_lookup(phone_number)
    if mms_info and mms_info['status'] == 'success':
        print(f"Information gathered via MMS or other protocols: {mms_info['info']}")
    else:
        print("No information gathered via MMS or other protocols.")

    phone_info = get_phone_info(phone_number, config.get('twilio_sid'), 
                                 config.get('twilio_token'), 
                                 config.get('telynx_token'))
    
    if phone_info:
        print(f"Country code for the phone number: {phone_info['country_code']}")
        if 'suburb' in phone_info:
            print(f"Suburb: {phone_info['suburb']}")
        if 'location' in phone_info:
            print(f"Location: {phone_info['location']}")
        if 'carrier' in phone_info:
            print(f"Carrier: {phone_info['carrier']}")

    # Menu for call options
    print("\nSelect the service to use:")
    print("1. Telynx")
    print("2. Twilio")
    print("3. Search Google")
    print("4. Search DuckDuckGo")
    service_choice = input("Enter your choice (1, 2, 3, or 4): ")

    call_response = None  # Initialize call_response to avoid UnboundLocalError

    if service_choice == '1':
        caller_number = config['telynx_number']
        call_response = call_number(phone_number, caller_number, telynx_token=config['telynx_token'])
    elif service_choice == '2':
        caller_number = config['twilio_number']
        call_response = call_number(phone_number, caller_number, twilio_sid=config['twilio_sid'], twilio_token=config['twilio_token'])
    elif service_choice == '3':
        # Create a search link for Google
        google_search_url = f"https://www.google.com/search?q={phone_number}"
        print(f"You can search for the number on Google here: {google_search_url}")
    elif service_choice == '4':
        # Create a search link for DuckDuckGo
        duckduckgo_search_url = f"https://duckduckgo.com/?q={phone_number}"
        print(f"You can search for the number on DuckDuckGo here: {duckduckgo_search_url}")
    else:
        print("Invalid choice. No action will be taken.")

    if call_response:
        # Process call response if needed
        print("Call response:", call_response)

if __name__ == "__main__":
    main()
