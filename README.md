# Adaptive User Interface in Mixed Reality in Populated Environment
## Repository Introduction
This repository is for the dissertation "Adaptive User Interface in Mixed Reality in Populated Environment" by **Zhaoqi Chen**, supervised by **Prof. Anthony Steed** at **University College London (UCL)**. There are three folders: DataAnalysis, Passthrough_Sample and AdaptiveUI(MR), the first one is the source code for data analysis of the report, including data exploration, descriptive and statistical analysis; the second one is the prototype for real human detection using Meta Passthrough Camera API and YOLOv9; the last one is the main implementation of the project, including avatar simulation, UI detection and Simon game logic.

## Abstract
Mixed reality (MR) interfaces are typically spatially anchored within the user’s environment, which can lead to visual occlusion of nearby individuals in socially populated settings. This may reduce users’ situational awareness and negatively affect interaction quality. This dissertation investigates whether adaptive user interface (UI) movement can mitigate such occlusion and improve user experience in MR environments.
An adaptive UI repositioning mechanism was designed to dynamically adjust interface placement based on potential visual interference with nearby individuals. The system was implemented in a controlled MR prototype and evaluated through a user study with 20 participants across three conditions: static UI, leftward adaptive movement, and upward adaptive movement. The results suggest that while adaptive UI improves users’ attention towards social interactions, it does not necessarily translate into enhanced perceived usability or comfort. This work contributes empirical evidence and design insights for adaptive UI in MR, emphasising the importance of balancing environmental awareness, user comfort, and task-focused interaction in the design of socially aware interfaces.

## Data Confidentiality
The DataAnalysis folder concludes pure python scripts only. The other two folders are Unity projects which include Unity config files, assets, and C# scripts which are the main code.

## Ethics
The user study was approved by the UCL Computer Science Research Ethics Committee (Project ID: UCL/CSREC/R/16), Data collection was done anonymously and all collected data were stored to protect participants’ data confidentiality. No identification information was collected.
