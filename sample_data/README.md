# Sample Data & Deterministic Demo Mode

This directory contains deterministic sample data and synthetic media generators for evaluating the **Multimodal Attendance & Engagement Agent**.

## Privacy Assurance
- **Zero Real Student Media:** No real student facial images, biometric vectors, or audio recordings are stored in this repository.
- **Deterministic Simulation:** When running in **Demo Mode**, the application uses a predefined mathematical model of classroom dynamics (600-second session, 8 registered students, realistic motion fluctuations, and audio silence intervals).
- **Synthetic Media Generator:** The module `modules.demo_data.generate_synthetic_media()` programmatically constructs a 10-second test video (`sample_classroom_10s.mp4`) and test audio (`sample_classroom_10s.wav`) directly using OpenCV drawing functions and mathematical sine waves. This allows evaluators to verify the complete video and audio extraction pipelines without requiring an external camera.

## How to Test Demo Mode
1. Launch the Streamlit application:
   ```bash
   streamlit run app.py
   ```
2. On the **Home Dashboard**, click **"Load Deterministic Demo Session"**.
3. Navigate to **Analytics Dashboard** (`pages/1_Dashboard.py`) or **Reports** (`pages/4_Reports.py`) to explore:
   - Multimodal engagement timelines.
   - Attendance status donut chart and track duration bars.
   - Prolonged silence interval markers.
   - AI pedagogical recommendations with evidence and caveats.
   - Downloadable attendance CSV, JSON summaries, and markdown executive reports.
