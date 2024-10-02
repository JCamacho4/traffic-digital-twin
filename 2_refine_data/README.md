## Data Refinement

This section handles the refinement of raw traffic data.

### Instructions
1. Navigate to the `2_refine_data` folder.
2. Move the `.json` files extracted from the first part into the `data` folder inside the `2_refine_data` directory.
3. Fill in the `.env` file with your API and MongoDB credentials.
4. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
5. Run the refinement process:
    ```bash
    python main.py
    ```
This will clean the data and store it in your MongoDB database under the collections `TFG -> graphs` and `TFG -> dates`.

### MongoDB Database Setup
This section handles the collection and refinement of raw data.

If you prefer not to collect data manually, pre-collected data files (`TFG.dates.json` and `TFG.graphs.json`) are provided in this repository.

### To Import Data into MongoDB:
1. Ensure your MongoDB instance is running.
2. Use the following commands to import the provided `.json` files:
    ```bash
    mongoimport --db TFG --collection dates --file TFG.dates.json
    mongoimport --db TFG --collection graphs --file TFG.graphs.json
    ```
