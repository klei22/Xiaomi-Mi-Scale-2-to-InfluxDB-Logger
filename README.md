# Xiaomi Mi Scale 2 to InfluxDB Logger

This project provides a Python script to read weight data from a **Xiaomi Mi
Body Composition Scale 2** using Bluetooth Low Energy (BLE) and logs the data
to **InfluxDB** for storage and analysis.

## Features

- Reads weight measurements (in kg and lbs) from the Xiaomi Mi Scale 2.
- Validates that the weight is within expected range (defaults to 50 kg and below 300 lbs).
- Sends data to InfluxDB at most once every 10 seconds to prevent excessive data logging.
- Uses asynchronous BLE scanning for efficient device discovery and data reading.

## Prerequisites

- **Python 3.7** or higher.
- A **Xiaomi Mi Body Composition Scale 2**.
- A computer with **Bluetooth Low Energy (BLE)** capabilities.
- An **InfluxDB** instance running and accessible.
- Internet connection (if InfluxDB is hosted remotely).

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/klei22/xiaomi-scale-influxdb.git
   cd xiaomi-scale-influxdb
   ```

2. **Set Up a Python Virtual Environment (Optional but Recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the Required Python Packages**

   Install the dependencies listed in `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

   This will install:

   - `bleak==0.22.3`: For BLE communication.
   - `influxdb_client==1.47.0`: For interacting with InfluxDB.

## Configuration

### 1. Obtain Your Scale's MAC Address

You need to know your scale's BLE MAC address to configure the script.

- **Option A: Use a BLE Scanner App**

  - Install a BLE scanner app on your smartphone (e.g., "nRF Connect" for Android or iOS).
  - Turn on Bluetooth and open the app.
  - Step on your scale to activate it.
  - Look for a device named "MIBFS" or similar in the app.
  - Note the MAC address (e.g., `AA:BB:CC:DD:EE:FF`).

- **Option B: Use a Command-Line Tool**

  - On Linux, you can use `hcitool` or `bluetoothctl`.
  - Step on your scale to activate it.
  - Run `bluetoothctl` and use `scan on` to find the scale.
  - Note the MAC address.

### 2. Configure the Scale's MAC Address

- **Rename `device_address_template.py` to `device_address.py`:**

  ```bash
  mv device_address_template.py device_address.py
  ```

- **Edit `device_address.py`:**

  Open `device_address.py` in a text editor and replace `AA:BB:CC:DD:EE:FF` with your scale's MAC address:

  ```python
  device_address = "AA:BB:CC:DD:EE:FF"  # Replace with your scale's MAC address
  ```

### 3. Set Up InfluxDB

Ensure that you have an InfluxDB instance running. You can run InfluxDB locally using Docker or install it directly.

- **Docker Example:**

  ```bash
  docker run -p 8086:8086 \
    -v $PWD/influxdb:/var/lib/influxdb2 \
    -e DOCKER_INFLUXDB_INIT_MODE=setup \
    -e DOCKER_INFLUXDB_INIT_USERNAME=my-user \
    -e DOCKER_INFLUXDB_INIT_PASSWORD=my-password \
    -e DOCKER_INFLUXDB_INIT_ORG=my-org \
    -e DOCKER_INFLUXDB_INIT_BUCKET=health_data \
    -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token \
    influxdb:latest
  ```

  - Replace `my-user`, `my-password`, `my-org`, `health_data`, and `my-super-secret-auth-token` with your desired values.

- **Note:** The bucket name in this script is `health_data`. Ensure that it matches the bucket you create in InfluxDB.

### 4. Configure InfluxDB Credentials

- **Set the InfluxDB Token as an Environment Variable:**

  ```bash
  export INFLUXDB_TOKEN='my-super-secret-auth-token'
  ```

  - Replace `'my-super-secret-auth-token'` with your actual InfluxDB token.

- **Alternatively, you can set the token in your shell profile** (e.g., `.bashrc`, `.zshrc`) for persistence.

- **Verify InfluxDB Configuration in the Script:**

  Open `log_weight_to_influxdb.py` and ensure the following variables match your InfluxDB setup:

  ```python
  BUCKET = "health_data"        # The bucket you set up in InfluxDB
  ORG = "my-org"                # Your InfluxDB organization
  URL = "http://localhost:8086" # InfluxDB URL
  ```

## Usage

1. **Activate Your Virtual Environment (if you created one):**

   ```bash
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. **Run the Script:**

   ```bash
   python log_weight_to_influxdb.py
   ```

3. **Step on the Scale:**

   - Ensure your Bluetooth adapter is enabled and functioning.
   - Step on your Xiaomi Mi Scale 2 to activate it.
   - The script will scan for the scale, read the weight data, and log it to InfluxDB.

## Expected Output

```plaintext
Scanning for Xiaomi Mi Body Composition Scale 2...
Found Xiaomi Mi Scale 2 at address: AA:BB:CC:DD:EE:FF
Listening for weight data...
Weight data sent to InfluxDB: 2023-10-05T14:30:00.123456Z, Weight: 70.50 kg, 155.43 lbs
------------------------------
Waiting for 10 seconds after successful send.
```

## Data Verification

- **Access InfluxDB UI:**

  - Open your web browser and navigate to `http://localhost:8086` (or your InfluxDB URL).
  - Log in with your credentials.

- **Use Data Explorer:**

  - Navigate to the **Data Explorer** section.
  - Select your bucket (`health_data`).
  - Run a query to view the data:

    ```flux
    from(bucket: "health_data")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "body_metrics")
    ```

  - You should see the weight data logged by the script.

## Troubleshooting

- **No Data Received:**

  - Ensure the scale is active and nearby.
  - Verify that the MAC address in `device_address.py` is correct.
  - Make sure no other devices (like smartphones) are connected to the scale.

- **Permission Errors:**

  - On Linux, you may need to run the script with `sudo` or adjust Bluetooth permissions.
  - Add your user to the `bluetooth` group or set appropriate permissions.

- **InfluxDB Connection Issues:**

  - Ensure InfluxDB is running and accessible at the specified URL.
  - Check that the bucket and organization names match your InfluxDB setup.
  - Verify that the `INFLUXDB_TOKEN` environment variable is correctly set.

- **Bluetooth Issues:**

  - Ensure your Bluetooth adapter is enabled and supported.
  - Install necessary drivers or firmware updates if needed.

## Customization

- **Adjusting Weight Range:**

  - The script only logs weight measurements above 50 kg and below 300 lbs.
  - To adjust these thresholds, modify the condition in `log_weight_to_influxdb.py`:

    ```python
    if weight_kg > 50 and weight_lbs < 300:
        # Process and log data
    ```

- **Changing Measurement Frequency:**

  - The script sends data to InfluxDB at most once every 10 seconds.
  - To change this interval, modify the `10` in the time check:

    ```python
    if current_time - last_send_time >= 10:
        # Send data
    ```

- **Logging Additional Data:**

  - If you wish to log more data (e.g., impedance, body composition), you can modify the script to include additional fields.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the developers of the `bleak` and `influxdb_client` libraries for their excellent tools.
- Inspired by projects integrating Xiaomi Mi Scale with various data platforms.

## Disclaimer

- This script is intended for personal use and educational purposes.
- The data and calculations are based on reverse-engineered protocols and may not be medically accurate.
- Always consult a healthcare professional for health-related assessments.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

