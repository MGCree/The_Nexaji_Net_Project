# 🌐 The Nexaji Net Project

> “To create a decentralized version of the internet, freeing us from limitations and corruption.”

---

## 🧠 Overview

**The Nexaji Net Project** aims to redefine how digital networks operate by simulating and ultimately constructing a decentralized, self-healing web of interconnected nodes.  
Unlike traditional centralized systems, Nexaji Net envisions a future where the flow of information is independent, resilient, and resistant to control or interference.

Currently in its **early prototyping phase**, the project focuses on simulating nodes, connections, and network behaviors through a visual environment powered by **PySide6**.

---

## ⚙️ Core Concept

At its heart, Nexaji Net represents a network where each node operates semi-autonomously — capable of maintaining, rebuilding, and routing around faults.  
Every node stores its state and relationships in a local JSON structure, forming the groundwork for a distributed persistence layer.

This design provides a foundation for future implementations involving:
- Dynamic peer-to-peer routing  
- Self-healing protocols  
- Data redundancy and decentralization  

---

## 🎨 Features (in progress)

- **🩹 Self-Healing Network Simulation**  
  Nodes automatically detect broken or delayed connections and re-establish routes to maintain continuity.

- **📦 Node Data Persistence**  
  Each node maintains its own JSON-based record of connections, delays, and states.

- **🔺 Special Node Types**  
  Support for different node roles such as “server” or “relay,” represented with unique visual shapes (rectangular for standard nodes, hexagonal for special ones).

- **🧩 Expandable Design**  
  The architecture supports modular growth — additional protocols, encryption layers, and AI-based optimization can be integrated later.

---

## 🖥️ Current Technical Stack

- **Language:** Python 3  
- **Framework:** PySide6 (Qt for Python)  
- **Storage:** Local JSON-based node state files  
- **Rendering:** Custom network visualization canvas  

---

## 🚧 Development Status

> **Stage:** Prototype / Simulation Phase  
> **Focus:** Core logic, node rendering, and connection management.  

Future work will include:
- Implementing real network packet simulation  
- Synchronization between independent instances  
- UI enhancements for dynamic visualization  
- Transitioning from simulation to functional distributed networking  

---

## 🕳️ Vision Statement

> “The Nexaji Net will stand as a free and self-sustaining digital realm —  
> immune to central failure, censorship, and control.”

---

## 👤 Author

**Jakub Jankowski**  
Creator and lead developer of *The Nexaji Net Project*.  

This project originated as part of a **university research and development objective**, exploring decentralized systems, self-healing networks, and the potential for next-generation digital infrastructure.

---

## 📜 License

Copyright © 2025
Jakub Jankowski — The Nexaji Net Project
All rights reserved.

This repository and its contents are made publicly visible for educational and demonstrative purposes only.
No part of this project may be copied, modified, distributed, or used in any software, product, or service, whether commercial or non-commercial, without explicit written permission from the author.

You are free to:

View and explore the source code.

Run the software for personal, non-commercial testing purposes.

You may not:

Copy or redistribute this software or its components.

Modify or use this software in derivative works.

Claim ownership, authorship, or affiliation with this project.

This restriction will remain in effect until an open-source license (such as MIT or GPLv3) is officially published for this project.
The license update is likely to happen once the project is in a stable usable state with most or all features implemented and tested.

For further info please contact at: creemeister@icloud.com

---
