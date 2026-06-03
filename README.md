# 🪐 3D Planet Colonizer

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
