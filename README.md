# PathFinding-Agent

## Overview
An interactive grid-based pathfinding agent that implements A* Search and 
Greedy Best-First Search (GBFS) with real-time dynamic obstacle re-planning.

## Features
- A* Search and Greedy Best-First Search (GBFS)
- Manhattan and Euclidean distance heuristics
- Dynamic obstacle spawning with live re-planning
- Interactive grid editor (draw walls, place start/goal)
- Random maze generation (30% wall density)
- Live metrics: nodes expanded, path cost, execution time

## How to Run
**Install dependency:**
```
pip install pygame
```
**Run the program:**
```
python pathfinding_agent.py
```

## Controls
| Action | Method |
|--------|--------|
| Place Start node | Left-click (1st click) |
| Place Goal node | Left-click (2nd click) |
| Draw walls | Left-click and drag |
| Erase node | Right-click |
| Run search | Click Run Search or Space |
| Dynamic mode | Click Dynamic Mode or D |
| Random maze | Click Random Maze or R |
| Clear board | Click Clear Board or C |
| Resize grid | + / − buttons or ↑ ↓ keys |
| Toggle algorithm | A* or GBFS buttons |
| Toggle heuristic | Manhattan or Euclidean buttons |

## Algorithms
- **A* Search** — f(n) = g(n) + h(n), guarantees optimal path
- **GBFS** — f(n) = h(n), faster but not always optimal
