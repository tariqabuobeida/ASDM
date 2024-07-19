
# Interactive Web-Mapping Murder-Mystery Game

## Overview
This repository contains the code and resources for an interactive, web-based murder-mystery game that allows users to explore geographical spaces. The game is built upon an object-relational database system with spatial queries to support the web application.

## Game Design
The game is designed to immerse players in key areas within Edinburgh, where they navigate through the environment to complete four main puzzles and solve the overarching mystery. The narrative unfolds progressively as the user traverses the space, following one of the main characters - **Tom**, **Tarig**, or **Sitong**. The objective is to uncover the reasons behind the sudden reappearance of the removal of **William M** from the School of Geosciences by investigating prime suspects **Bruce G**, **Neil S**, and **Zhiqiang F**.

## Technological Frameworks
- **Oracle Spatial:** Manages complex spatial queries and efficient data storage, supporting a variety of geometric types and spatial operations.
- **Python with Flask:** Handles server-side logic and database connections, hosting data retrieved from Oracle in GeoJSON format.
- **Leaflet:** Enables successful web-map deployment and enhances real-time user interaction.
- **JavaScript:** Enhances client-side scripting for improved user interaction and functionality.

## Objectives
The primary objectives of this project are:
- To integrate Oracle Spatial’s advanced data management capabilities with interactive web technologies for storing, querying, and manipulating geographic information.
- To demonstrate advanced spatial querying to develop effective application mechanics, including responsive user interaction.

## Getting Started

### Prerequisites
- [Oracle Database](https://www.oracle.com/database/)
- [Python](https://www.python.org/) (with Flask framework)

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/murder-mystery-game.git
   cd murder-mystery-game
   ```

2. **Set up the Oracle Database:**
   - The game uses a database developed at the University of Edinburgh, School of Geosciences, hosted on the `geoslearn` database server.
   - Create the necessary tables and insert spatial data as described in the `/database` directory.
   - Ensure Oracle Spatial features are enabled.

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the Flask server:**
   - Configure the database connection in `config.py` to connect to the `geoslearn` database server.
   - Run the server:
     ```bash
     python app.py
     ```

5. **Run the application:**
   - Open your browser and navigate to `http://localhost:5000`.

## Usage
Players navigate through the game environment by solving puzzles and following clues to progress the narrative. Each area within Edinburgh has been meticulously mapped using spatial data to create an immersive experience.

## Contributors
- **Tarig Ali**
- **Tom Burnett**
- **Sitong Yu**

## Contributing
Contributions are welcome! Please fork the repository and submit pull requests for any improvements or bug fixes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- The University of Edinburgh, School of Geosciences, for hosting the `geoslearn` database.
- **Bruce Gittings** for his guidance and support.
- The team members and collaborators who contributed to the project.
