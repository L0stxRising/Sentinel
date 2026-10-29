## SENTINEL

AIM: Build a low-cost, smart underground drain monitoring network that predicts water blockages and alerts municipal

authorities before street flooding occurs.

PROBLEM STATEMENT: Every monsoon, city drains get clogged with plastic, silt, and garbage, causing severe waterlogging, traffic gridlock, and the spread of dangerous diseases like dengue and cholera. Right now, authorities only clean drains after water overflows onto the streets. Sanitation workers are then forced to risk their lives diving into toxic, flooded drains during emergency cleanups. This project will help cities catch blockages days before an overflow happens, making drain maintenance planned, safe, and cost-effective.

## MATERIAL USED:

- Radar Water Sensor: To measure the water level inside the manhole without touching dirty sewage.

- Microcontroller Board: To handle sensor readings and manage power-saving deep sleep modes.

- LoRa Transceiver Modules: For long-range radio communication.

- Lithium Battery Pack: To power each underground node for up to 2 years using deep-sleep cycles.


- Central Server / AI Model (LSTM): To store historical water flow data and analyze drainage Trends over time.


## HOW THE PROJECT WORKS:

The Sentinel system follows a continuous 5-step cycle to monitor drains and predict floods:

- Sense: The ultrasonic sensor measures the water level without touching the sewage, then enters deep sleep to save battery.

- Communicate: LoRa sends the reading through the node network, automatically rerouting around failed nodes.

- Store: A gateway forwards the data to a central database, building a historical record of each drain.

- Think: The LSTM model compares current drainage patterns with historical behavior to detect unusually slow drainage that may indicate a developing blockage.

- Act: The system generates a risk score and alerts authorities through the dashboard, allowing them to act before an overflow occurs.


## The AI Model :

The AI model uses an LSTM (Long Short-Term Memory) network to learn the normal water-level behavior of each drain by analyzing historical data collected over hours, days, and weeks. Instead of relying on a fixed threshold, it studies the relationship between past and current readings to understand long-term patterns. This allows it to avoid falsely flagging a random upsurge or downsurge caused by temporary rainfall, sudden water flow, or other short-term fluctuations. The model focuses on persistent and unusual changes, such as water levels gradually rising or remaining elevated for longer than expected, which may indicate a developing blockage. When such an anomaly is detected, the system generates a risk score to indicate the likelihood of a potential blockage.


## UTILITY OF PROJECT-

- Prevents Urban Waterlogging & Traffic Jams: By predicting blockages days before heavy rainfall, authorities can clear drains early, preventing severe street flooding and citywide traffic gridlocks.

- Protects Public Health: Prevents stagnant sewage water from overflowing onto public roads, directly eliminating mosquito breeding grounds and preventing outbreaks of waterborne diseases like dengue and cholera.

- Safeguards Sanitation Workers: Replaces dangerous emergency drain-diving in toxic, flooded conditions with safe, planned maintenance interventions.

- Saves Municipal Funds: Shifts city maintenance from wasteful, fixed-schedule cleaning to targeted, condition- based cleaning, saving taxpayer money and optimizing labor.

- Provides Real-Time City Insights: Supplies municipal planners with historical flow data to identify chronically undersized or damaged drainage pipes across the urban network.

## UNIQUENESS AND NOVELTY-

- Predictive AI over Basic Alarm

- Underground Relay Network

- Custom Drain Baselines

- Low-Cost & Long Battery Life
