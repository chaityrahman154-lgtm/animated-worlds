# 🌍 Animated Worlds — Python Graphics & Game Simulations

A collection of interactive game projects and animated scenes built with **Python and OpenGL**, developed for **CSE 423 — Computer Graphics** at BRAC University. Each project translates core graphics theory — coordinate transformations, real-time rendering, scene composition — into something you can actually play or watch.

## ✨ Project Overview

Computer graphics is easier to understand when it moves. This repository holds a series of increasingly complex Python programs that bridge the gap between mathematical concepts (matrix transformations, projection geometry, the OpenGL pipeline) and live, real-time visual output.

Projects range from 2D gameplay to animated 3D environments, each demonstrating a distinct set of rendering techniques while telling a small visual story.

## 🎮 Projects

### 🏠 Building a House in Rainfall
An animated scene where a house is constructed on-screen while rain falls dynamically in the background. Demonstrates **layered scene rendering**, particle-style animation for rain, and hierarchical object drawing using `glPushMatrix`/`glPopMatrix`.

### 📦 Building the Amazing Box
A 3D box construction scene using OpenGL primitives — `GL_QUADS` and `GL_LINES` — with camera perspective to give the illusion of depth. Focuses on **3D coordinate systems**, face normals, and basic lighting setup.

### 🧬 Colony Survive
A survival simulation where colony entities must navigate a dynamic environment. Demonstrates **entity state management**, movement logic, and real-time scene updates within the OpenGL event loop.

## 🪐 3D Planet Colonizer

A 3D strategy-survival game where the player lands on an alien planet and must build a thriving colony while defending against devastating meteor showers. Developed as a 3D Group Project for CSE 423 (Computer Graphics).

## ✨ Project Overview
Players act as colony commanders on a grid-based alien terrain. You must carefully manage resources to place structures (Housing, Mines, and Shield Towers) while defending your colony from increasingly intense waves of falling meteors. The game requires strategic placement, rapid repairs, and quick camera switching to survive. The game ends when all lives are lost.

This project heavily utilizes the **PyOpenGL** pipeline, demonstrating real-time game logic, hierarchical transformations (`glPushMatrix`/`glPopMatrix`), collision detection, and custom multi-mode camera systems using `gluLookAt`.

## 🎮 Game Mechanics & Controls

### Building & Economy
* **W/A/S/D:** Move the placement cursor across the grid.
* **1:** Place Housing (Blue Cuboids) - Increases population score.
* **2:** Place Mine (Yellow Cylinders) - Generates resources over time when placed near resource nodes.
* **3:** Place Shield Tower (Green Spheres) - Projects a protective dome that destroys incoming meteors.
* **U:** Upgrade a building (increases size/efficiency).
* **E:** Repair a damaged building before it is destroyed by a second meteor hit.

### Camera Modes (Right-Click to Toggle)
* **Overview Mode:** Top-down angled view of the colony.
* **Builder Mode:** Low-angle view following the cursor for precise placement.
* **Cinematic Mode:** Auto-orbiting camera showcasing the entire environment.
* **Arrow Keys:** Adjust camera height and manual rotation.

## 🧑‍💻 Core Systems & Technical Implementation

**Building System & Resource Management**
* Implemented the grid-based cursor and placement system.
* Handled economy logic, resource node spawning, and smooth `glScalef` animations for building construction and upgrades.

**Meteor System, Defense & Collision**
* Engineered the dynamic meteor wave system with increasing difficulty and `glRotatef` animations.
* Developed spatial collision detection between meteors, shield radii, and ground structures.
* Created visual particle/explosion effects for impacts.

**Camera, Terrain, HUD & Game Flow**
* Designed the 3D environment with alternating `GL_QUADS` grid cells and a dynamic day/night cycle via `glClearColor` interpolation.
* Programmed the custom 3-mode camera system manipulating `gluLookAt` parameters.
* Built the fully functional Heads-Up Display (HUD) utilizing `draw_text` for real-time stats and game over states.


### 🕹️ 2D Game
A playable 2D game with movement, collision detection, and a game loop. Explores **2D coordinate mapping**, keyboard input via GLUT callbacks, and screen boundary logic.

### 🌐 3D Game
Extends into 3D gameplay — demonstrates **perspective projection**, `gluLookAt` camera positioning, and 3D object interaction within a live scene.

## 🧑‍💻 Core Technical Concepts Demonstrated

- OpenGL rendering pipeline (CPU → GPU draw calls)
- `glPushMatrix` / `glPopMatrix` for hierarchical scene graphs
- `gluLookAt` and camera positioning in 3D space
- `glRotatef`, `glTranslatef`, `glScalef` — real-time transformations
- GLUT keyboard and timer callbacks for interactivity
- 2D and 3D spatial collision detection
- Particle-style animation (rainfall effects)

## 🚀 Getting Started

```bash
pip install PyOpenGL PyOpenGL_accelerate pygame
python "Building a House in Rainfall.py"
python "2D Game.py"
```

> Requires a display environment. Run on a local machine with a GPU or configure a virtual display on Linux.

## License
MIT License — see `LICENSE` for details.
