## ✈️ Fly-Easy ✈️

This is an interactive and dynamic airport and travel companion app that allows the user to store their boarding passes, book hotels, order food from airport restaurants, track flights, and plan a multi-day vacation using the app's AI trip planner, or as we like to call it, the "Easy-Planner".

The tech stack used is a React Native frontend with a Python backend connected by Flask, enabling efficient handling of user queries. The primary focus of this project lies in the classical AI algorithms written for user inputs, and for general awareness of user surroundings.

The Easy-Planner employs a greedy, constraint-aware planning strategy that incrementally builds daily schedules by prioritizing high-interest activities while strictly enforcing hard constraints such as time availability and age eligibility. When hard-constraint violations arise, the planner attempts a limited number of repair operations to accommodate activities when feasible. Activities violating soft constraints such as budget limits, activity repetition, and group satisfaction, are handled by the penalty-based scoring, allowing the planner to balance competing preferences without producing unrealistic plans.

What differentiates our planner from traditional trip planners is its emphasis on human-like decision-making. Activities are evaluated not only by overall interest, but also by duration and similarity to previously-scheduled events. In cases where interest levels vary significantly, the planner explicitly accounts for “extreme interest” scenarios, ensuring that minority preferences are considered fairly without overwhelming the overall experience.

### Setup:

1. Clone this repository.
2. Open a terminal with the root directory as the working directory.
3. Navigate to ```.\client``` directory and run ```npm install``` (Make sure ```Node.js``` is installed first!).
4. Run ```npx expo start``` or ```npm start```.
5. Open up a new terminal with the project root as the working directory.
   * If a ```.venv``` does not exist in this project, install it using the command based on your operating system.
     * **Windows**: ```python -m venv .venv```
     * **Mac/Linux**: ```python3 -m venv .venv```
6. **Activate ```.venv```** - In the same terminal, run:
   * **Windows**: ```.\.venv\Scripts\Activate.ps1```
   * **Mac/Linux**: ```source .venv\bin\activate```
7. On this terminal, navigate to ```.\client\src\backend```
8. Run the command ```python app.py``` (If this does not work on Mac/Linux, run ```python3 app.py```)
9. Now you must have two terminals running:
    1. **Frontend terminal**: you will see a QR-code along with a few keyboard shortcuts below it.
    2. **Backend terminal**: the terminal you just started ```app.py``` with.
10. Switch to the frontend terminal, then explore the options for app usage. Our two recommendations are:
    1. **Web browser**: Press `w` on your terminal to explore the application on a web browser 
        
       (**note**: you will not be able to store your boarding passes on your digital wallet this way).
    2. **Mobile application**: Scan the QR code on your terminal to explore the application on mobile. 
       * For iOS, use the QR-code scanner. 
       * For Android, use the builtin Expo Go scanner. 
    * **Note**: Since this project is currently not fully deployed, there is no hosted backend. If you would like to use the full potential of the mobile application, replace the ```localhost``` in the fetches with your IPV4 address. (Optional)
