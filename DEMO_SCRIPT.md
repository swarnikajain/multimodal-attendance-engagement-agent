# Demonstration Video Presentation Script (3–5 Minutes)
## Multimodal Attendance & Engagement Agent
**Platform:** FutureSkills Prime AI/ML Evaluation  
**Target Duration:** 3 minutes 30 seconds to 4 minutes 30 seconds  
**Recording Mode:** Desktop Screen Recording (1080p, 30fps) with Voiceover  

---

## 📋 Pre-Recording Setup Checklist
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run automated tests to verify clean environment: `python -m pytest tests/`
- [ ] Launch application in browser: `streamlit run app.py`
- [ ] Set browser zoom to 100% or 110% for crisp text readability.
- [ ] Clear test uploads or previous sessions if needed (`Settings > Clear All Temporary Media Files`).
- [ ] Keep audio input clear, microphone positioned 6–8 inches away.

---

## 🎬 Minute-by-Minute Video Walkthrough

### 1. Introduction & Problem Statement [0:00 – 0:30]
- **Visual:** Display **Home Dashboard** (`app.py`). Show the header card *"Multimodal Attendance & Engagement Agent"*, the local badges, and ethical disclosure banner.
- **Spoken Script:**
  > "Hello evaluators! Welcome to the demonstration of the **Multimodal Attendance & Engagement Agent**, an AI-powered, privacy-conscious classroom intelligence system designed for local deployment.
  > 
  > Traditional roll-calls waste instructional time, while modern cloud surveillance tools raise severe data privacy and biometric concerns. Furthermore, conventional systems often make unsupported claims about student attention. 
  > 
  > Our solution addresses this by combining **on-device computer vision** and **acoustic signal processing** to automate attendance and measure observable physical and acoustic dynamics—while operating with 100% local privacy, zero cloud transmission, and transparent ethical disclosures."

---

### 2. Home Dashboard & Quick Actions [0:30 – 1:00]
- **Visual:** Point mouse across the 4 KPI cards (Analyzed Sessions, Registered Participants, Avg Attendance Rate, Avg Engagement Proxy). Click the expander *"Ethical Transparency & Observational Metric Limitations"*.
- **Spoken Script:**
  > "Here on the Home Dashboard, instructors get an immediate overview of class sessions and aggregate metrics. 
  > 
  > Crucially, our system features an upfront ethical disclosure: our engagement indicators are **observational proxies** of motion, presence, and audio energy. They **never** claim to read a student's internal thoughts, mental states, or emotional comprehension.
  > 
  > Let's click **'Seed Sample Student Roster'** to populate our class directory with registered students, and click **'Load Deterministic Demo Session'** to instantly seed a full 10-minute simulated dataset for evaluation."

---

### 3. Participant Management [1:00 – 1:30]
- **Visual:** Navigate to sidebar > **"2 👥 Participants"**. Show the Roster table with 8 students. Show the "Register New Participant" and "Batch Import Roster (CSV)" tabs.
- **Spoken Script:**
  > "Under **Participant Management**, instructors manage their student rosters with standard identifiers like ID, name, email, and department. 
  > 
  > Adhering to privacy-by-design, our system **never stores raw face photos or biometric vector templates**. Instructors can register individual students or import an entire course roster via CSV using our provided template."

---

### 4. Session Setup & Media Processing Pipeline [1:30 – 2:15]
- **Visual:** Navigate to **"3 🎯 Session Analysis"**. Show Session Setup fields. Check *"Use Built-in 10-Second Test Media Sample"*, toggle the Privacy Authorization checkbox, and click *"Start Multimodal Analysis"*. Show the progress bar advancing through video frame sampling, face detection, centroid tracking, and acoustic signal processing.
- **Spoken Script:**
  > "In **Session Setup**, an instructor configures a class session, adjusts the frame sampling interval to optimize laptop performance, and uploads class video or audio. 
  > 
  > To allow immediate evaluation on any laptop without uploading private classroom recordings, we also built a **Built-in Test Media Generator**. It generates genuine test video and audio files programmatically using OpenCV and acoustic wave synthesis.
  > 
  > After confirming privacy authorization, we trigger the local analysis. Watch the real-time pipeline: OpenCV extracts frames at configurable intervals, runs Haar cascade face detection, matches centroids across frames to build continuous tracks, and Librosa/SoundFile measures RMS audio energy and silence periods."

---

### 5. Automated Attendance & Identity Verification [2:15 – 2:50]
- **Visual:** Switch to the *"Review & Confirm Attendance"* tab. Highlight the provisional attendance table, the sustained presence rules, and the track-to-student mapping form. Select `Track-001`, map to student `STU101 - Aarav Sharma`, and click *"Save Mapping & Confirm Attendance"*.
- **Spoken Script:**
  > "Now let's examine the **Attendance Pipeline**. Computer vision alone detects bounding boxes and maintains anonymous track IDs like `Track-001`. To prevent hallucinated identity matches, the system applies a **sustained-presence rule**: transient, single-frame false detections are filtered out, while sustained observations >= 30% of the session are classified as Present.
  > 
  > Crucially, attendance remains **provisional** until an authorized instructor verifies the mapping. Using our verification interface, the instructor maps `Track-001` to `Aarav Sharma` and confirms attendance with a single click. The verified roster can be exported as a standard CSV report."

---

### 6. Interactive Multimodal Visualizations [2:50 – 3:30]
- **Visual:** Navigate to **"1 📊 Dashboard"**. Point out the *"Deterministic Demo Mode Active"* badge. Scroll through:
  1. Multimodal Engagement & Activity Dynamics Timeline (hover to show tooltip).
  2. Attendance Donut Chart and Track Duration Horizontal Bar Chart.
  3. Data Quality & Recording Diagnostics Card.
  4. Cross-Session Comparison Chart.
- **Spoken Script:**
  > "Moving to the **Analytics Dashboard**, Plotly renders high-resolution, interactive charts. 
  > 
  > The **Multimodal Dynamics Timeline** charts our transparent engagement proxy formula—a weighted fusion of visual presence, observable motion, and audio energy. Notice how prolonged silence intervals are automatically flagged with shaded red spans.
  > 
  > Next, our **Track Duration Chart** compares each student's observed time against the total lecture length. 
  > 
  > Furthermore, our **Data Quality Score** evaluates lighting, motion blur, and acoustic clipping so instructors know whether the recording conditions were optimal."

---

### 7. Explainable AI Recommendations & Reports [3:30 – 4:05]
- **Visual:** Navigate to **"4 📑 Reports"**. Show the AI Pedagogical Suggestions cards (Prolonged Silence, Mid-Session Engagement Dip, Continuous Lecture). Show the download buttons (CSV, JSON, Markdown). Click on the Markdown and JSON tabs.
- **Spoken Script:**
  > "Under **Reports**, our local rule-based **AI Recommendation Engine** provides explainable, non-punitive pedagogical suggestions. 
  > 
  > Each recommendation contains four critical elements:
  > 1. The exact observation that triggered it,
  > 2. The verifiable timestamped metric,
  > 3. An actionable teaching suggestion (such as introducing a think-pair-share or concept checkpoint), and
  > 4. An essential pedagogical caveat—reminding instructors that silence often indicates deep focus or exam solving rather than disengagement.
  > 
  > Instructors can download the attendance CSV, the complete session JSON schema, or an executive markdown report."

---

### 8. Privacy Architecture & Closing [4:05 – 4:30]
- **Visual:** Navigate to **"5 ⚙️ Settings"**. Show the Privacy Audit cards (100% Local, 0 Cloud Calls, Biometric Vectors Disabled) and the Temporary Media Cleanup button. Return to the Home Dashboard.
- **Spoken Script:**
  > "Finally, **Settings** verifies that zero bytes of data were transmitted externally, with controls to purge temporary media files at any time.
  > 
  > In conclusion, the Multimodal Attendance & Engagement Agent provides a complete, robust, and ethical educational intelligence tool that runs efficiently on standard laptop hardware without paid cloud APIs.
  > 
  > Thank you for your time and evaluation!"

---

## 📹 Post-Recording Checklist
- [ ] Check video resolution (minimum 1920x1080) and 30fps smoothness.
- [ ] Verify that cursor movements are smooth and deliberate.
- [ ] Verify that audio voiceover is audible and synchronized with screen actions.
- [ ] Export as MP4 (H.264 video codec, AAC audio codec).
- [ ] Upload to YouTube (Unlisted), Google Drive, or Loom, and insert the link into `README.md`.
