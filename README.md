# Traffic Flow Analysis & Simulation Tools 🚦

[![GitHub license](https://img.shields.io/github/license/JCamacho4/traffic-digital-twin)](LICENSE)
[![Python version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![MESA](https://img.shields.io/badge/MESA-ABM_Framework-green.svg)](https://mesa.readthedocs.io/en/stable/)
[![Dash](https://img.shields.io/badge/Dash-Plotly-yellow.svg)](https://dash.plotly.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-NoSQL-orange.svg)](https://www.mongodb.com/)

## Project Overview
This repository contains the final degree project for obtaining the title of **Software Engineer** at the **University of Málaga (UMA)**. The project received **honors** with a final grade of **9.4**. 

The goal of this project is to study traffic flow in a specific zone through data extraction, refinement, analysis, and simulation using a multi-tool system. The tools are built using Python with libraries like **MESA**, **DashPlotly**, and **MongoDB**.

### Key Features:
- **Automatic Data Collection**: Extract traffic data from the TomTom API using the Vector Flow Tiles Service to gather real-time and historical traffic information.
- **Data Refinement**: Clean and process the extracted data, converting it from GeoJSON format into a graph representation of the area. The data is then stored efficiently in MongoDB for further use.
- **Data Analysis Dashboard**: Visualize historical traffic trends through an interactive dashboard with various filters. The dashboard automatically generates analytical insights and visualizations, with the option to download the results.
- **Traffic Simulation Dashboard**: Simulate traffic behavior using an Agent-Based Model (ABM) and visualize detailed graphs of the simulation outcomes. The results can also be downloaded for further analysis.

## Project Structure
The project is organized into four distinct parts:

1. **extract_data**
2. **refine_data**
3. **data_dashboard**
4. **simulator_dashboard**

## Diagram of the App
The diagram below outlines the architecture and flow of the application:

![Application Diagram](./project_abstract_horizontal.drawio.png)

## Installation & Setup

### Prerequisites:
- Python 3.x
- MongoDB (Running instance)
- Clone this repository:
    ```bash
    git clone https://github.com/JCamacho4/traffic-digital-twin.git
    cd repo_name
    ```

### General Installation Steps:
Each part of the project is contained in its own folder, with specific installation and setup instructions. Please refer to the `README.md` file in each directory for detailed steps on how to configure and run that part of the project:

1. **1_extract_data**: Instructions for data extraction using the TomTom API.
   - [Go to extract data instructions](./1_extract_data/README.md)
   
2. **2_refine_data**: Instructions for refining and storing the collected data in MongoDB.
   - [Go to refine data instructions](./2_refine_data/README.md)
   
3. **3_data_dashboard**: Instructions for running the historical data analysis dashboard.
   - [Go to data dashboard instructions](./3_data_dashboard/README.md)
   
4. **4_simulator_dashboard**: Instructions for running the traffic simulation dashboard.
   - [Go to simulation dashboard instructions](./4_simulator_dashboard/README.md)

Before proceeding with each part, ensure you have installed the required Python libraries and filled in the necessary `.env` files as per the instructions in each respective folder.

## Research Paper
For detailed information about the research and methodologies behind this project, you can find the full paper [here](./paper.pdf).

## License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Acknowledgements
Special thanks to **Eduardo Guzmán** and **Juan Palma** for providing guidance.

Feel free to open issues, contribute, or contact me if you have any questions or suggestions.
