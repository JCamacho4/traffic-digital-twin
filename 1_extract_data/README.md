## Data Extraction

This section handles the collection of raw traffic data.

### Instructions

1. Navigate to the `1_extract_data` folder.
2. Fill in the `.env` file with your API credentials.
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Run the extraction script:
    ```bash
    python get_tile_info.py
    ```
5. Move the generated `.json` files into the `data` folder located inside the `2_refine_data` directory.
6. There is also raw data available in the `./month_rar` folder, containing information from May to August. If you want to use this pre-collected data, extract it and move the files to the same `data` directory, splitting them into `tile1` and `tile2` folders as needed.
