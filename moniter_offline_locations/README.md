Here’s a well-structured **`README.md`** for your project 👇

---

# Simple Network Monitor

A lightweight **asynchronous network monitoring tool** written in Python.
The script continuously pings devices (from a CSV list) and tracks their **online/offline status**.
It automatically records **outages per location**, detects recoveries, and stores all results in **daily JSON logs** and **rotating log files**.

---

## ✨ Features

* 🖧 **Ping monitoring**: Tracks availability of devices via ICMP ping.
* 📍 **Location-aware**: Each device is tied to a location (loaded from `devices.csv`).
* ⚠️ **Outage tracking**:

  * Detects when devices go offline.
  * Double-checks (retries) to prevent false alarms.
  * Records outage start/end time and total downtime duration.
* 📅 **Daily rollover**:

  * Creates a new log file for each day.
  * Carries over any active outages into the next day.
* 📂 **Persistent logs**:

  * Outage data saved as JSON (`outages/outages_YYYYMMDD.json`).
  * Runtime logs saved under `logs/monitor_YYYYMMDD.log`.
* ⏱️ **Configurable ping interval** (default: 30 seconds).
* 🛑 **Graceful shutdown** with Ctrl+C (saves current state before exit).

---

## 📂 Project Structure

```
.
├── devices.csv               # List of devices and their locations
├── outages/                  # Auto-created daily outage JSON files
├── logs/                     # Auto-created runtime logs
├── monitor.py                # Main monitoring script
└── README.md                 # Project documentation
```

---

## 📄 Input: `devices.csv`

Your CSV file should contain at least two columns:

```csv
location,device
Office,192.168.1.10
ServerRoom,192.168.1.20
Warehouse,10.0.0.5
```

* **location**: Human-readable name of where the device is.
* **device**: The IP address (or hostname) of the device to ping.

💡 **Tip**:
For each location, include the **modem/router IP** in the CSV.
That way, if the modem is offline, all devices at that location will naturally show as down.

---

## 🚀 Usage

1. Install Python 3.8+ (Linux/macOS/Windows).
2. Clone or copy this repository.
3. Prepare your `devices.csv` with locations and device IPs.
4. Run the monitor:

```bash
python3 monitor.py
```

Optional: change the ping interval inside `main()`:

```python
PING_INTERVAL = 3  # seconds
```

---

## 📊 Output

1. **Console summary (every cycle):**

```
[12:30:10] Online: 5, Offline: 2, Active outages: 2 (scan took 0.9s)
```

2. **Log file (`logs/monitor_YYYYMMDD.log`):**

```
2025-09-29 12:30:12 - WARNING - OUTAGE STARTED: Office (192.168.1.10) went offline at 12:30:12
2025-09-29 12:32:45 - INFO - RECOVERY: Office (192.168.1.10) back online at 12:32:45 (was offline for 2 minutes 33 seconds)
```

3. **Outage JSON (`outages/outages_YYYYMMDD.json`):**

```json
{
  "Office": [
    {
      "offline_at": "09/29/2025 12:30:12",
      "online_at": "09/29/2025 12:32:45",
      "offline_for": "2 minutes 33 seconds"
    }
  ]
}
```

---

## 🔧 Notes & Best Practices

* Always add **one device per modem/router** in your `devices.csv`.

  * If the modem is down, all devices behind it will appear offline, so monitoring the modem itself gives clarity.
* Use **short ping intervals** (e.g., 3–5 seconds) for real-time detection.
* Use **longer intervals** (e.g., 30–60 seconds) for less CPU/network load.
* Logs are automatically rotated **per day**.

---

## ⚖️ License

MIT License. Free to use, modify, and distribute.

---

