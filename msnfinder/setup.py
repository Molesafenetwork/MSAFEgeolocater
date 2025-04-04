import os
import subprocess
import sys
import pkg_resources

# List of required packages
required_packages = [
    'requests',
    'beautifulsoup4',
    'flask',
    'opencv-python',
    'numpy',
    'scrapy',  # Add Scrapy here
    'folium',   # Add Folium for mapping
    'geocoder',  # Add Geocoder for IP geolocation
    'phonenumbers'  # Add phonenumbers for phone number parsing
]

# Function to install and upgrade packages
def install_and_upgrade_packages():
    for package in required_packages:
        try:
            # Check if the package is already installed
            pkg_resources.require(package)
            print(f"{package} is already installed. Upgrading...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', package])
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            print(f"{package} is not installed. Installing...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Function to create the templates directory and HTML files
def create_templates():
    templates_dir = 'templates'
    os.makedirs(templates_dir, exist_ok=True)

    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Information Crawler</title>
</head>
<body>
    <h1>Information Gathering Tool</h1>
    <form method="POST">
        <label for="social_media">Social Media:</label>
        <input type="text" name="social_media" id="social_media"><br>
        <label for="phone_number">Phone Number:</label>
        <input type="text" name="phone_number" id="phone_number"><br>
        <label for="email">Email:</label>
        <input type="text" name="email" id="email"><br>
        <label for="name">Name:</label>
        <input type="text" name="name" id="name"><br>
        <label for="address">Address:</label>
        <input type="text" name="address" id="address"><br>
        <label for="mode">Mode:</label>
        <select name="mode" id="mode">
            <option value="endless">Endless</option>
            <option value="limited">Limited</option>
        </select><br>
        <label for="match_count">Match Count:</label>
        <input type="number" name="match_count" id="match_count" value="10"><br>
        <label for="min_score">Minimum Score:</label>
        <input type="number" name="min_score" id="min_score" value="50"><br>
        <button type="submit">Start Scraping</button>
    </form>
</body>
</html>
"""
    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write(index_html)

# Main function to run the setup
def main():
    print("Installing and upgrading required packages...")
    install_and_upgrade_packages()
    print("Creating templates directory and HTML files...")
    create_templates()
    print("Setup complete! You can now run your application.")

if __name__ == '__main__':
    main()