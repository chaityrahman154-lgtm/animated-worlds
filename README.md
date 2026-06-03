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
