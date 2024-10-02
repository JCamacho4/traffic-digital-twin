## Traffic Simulation Dashboard

This section provides a simulation dashboard that models traffic flow using an **Agent-Based Model (ABM)** powered by **MESA**. The dashboard allows users to visualize and analyze traffic behavior dynamically, offering insights into how different parameters affect traffic patterns.

### Instructions

1. Navigate to the `4_simulator_dashboard` folder.
2. Complete the `.env` files located in the base directory and inside the `traffic_model` folder.
3. Install the required dependencies in the base directory:
    ```bash
    pip install -r requirements.txt
    ```
4. Install the required dependencies inside the `traffic_model` directory (separate module):
    ```bash
    cd ./traffic_model
    pip install -r requirements.txt
    ```
5. Run the simulation dashboard from the `dash_gui` directory:
    ```bash
    python app.py
    ```
Access the simulation dashboard at `http://localhost:8050`.
