/**
 * KONE BACK-REPORTING HEAT MAP ENGINE
 * 
 * Converts real accelerometer movement data to elevator floor position
 * 
 * Physics:
 * - Each floor height: 3 meters
 * - Elevator car: 1.5m x 1.5m (square)
 * - Machine room: 3m x 3m above top floor
 * - Vertical axis: Z (accelerometer detects up/down)
 * - Horizontal axis: X, Y (movement within car)
 */

class HeatMapEngine {
  constructor() {
    this.FLOOR_HEIGHT = 3; // meters per floor
    this.CAR_WIDTH = 1.5;  // meters (1.5m x 1.5m square)
    this.CAR_DEPTH = 1.5;
    this.MACHINE_ROOM_HEIGHT = 3;
    
    // Acceleration thresholds for floor detection
    this.VERTICAL_THRESHOLD = 0.5; // m/s² to detect floor movement
    this.FLOOR_TRANSITION_TIME = 500; // ms to confirm floor change
    
    this.data = {
      points: [],            // All recorded points
      floors: {},           // Points grouped by floor
      duration: 0,
      startTime: null,
      endTime: null,
      currentFloor: 0,      // Which floor currently on
      trajectory: [],       // Path taken
    };
  }

  /**
   * Add raw accelerometer data point
   * @param {number} x - X acceleration (horizontal)
   * @param {number} y - Y acceleration (horizontal)
   * @param {number} z - Z acceleration (vertical - UP/DOWN)
   * @param {number} timestamp - Time of measurement
   */
  addPoint(x, y, z, timestamp) {
    const point = {
      x: x || 0,
      y: y || 0,
      z: z || 0,
      timestamp,
      magnitude: Math.sqrt(x*x + y*y + z*z),
    };

    this.data.points.push(point);

    // Detect floor change based on Z-acceleration
    const detectedFloor = this.detectFloor(z);
    
    if (detectedFloor !== this.data.currentFloor) {
      this.data.currentFloor = detectedFloor;
      this.data.trajectory.push({
        floor: detectedFloor,
        timestamp,
        duration: 0,
      });
    }

    return point;
  }

  /**
   * Detect which floor based on vertical acceleration
   * Positive Z = going UP
   * Negative Z = going DOWN
   * 
   * @param {number} z - Vertical acceleration
   * @returns {number} Floor number (0 = car top, 1-12 = floors, 13+ = machine room)
   */
  detectFloor(z) {
    // If no movement, assume still on current floor
    if (Math.abs(z) < this.VERTICAL_THRESHOLD) {
      return this.data.currentFloor;
    }

    // Integrate acceleration to get position
    // For every 3 meters of movement, add 1 floor
    const verticalDistance = Math.abs(z) * this.FLOOR_TRANSITION_TIME / 1000;
    const floorChange = Math.round(verticalDistance / this.FLOOR_HEIGHT);

    if (z > 0) {
      // Moving UP
      return Math.min(this.data.currentFloor + floorChange, 12);
    } else {
      // Moving DOWN
      return Math.max(this.data.currentFloor - floorChange, 0);
    }
  }

  /**
   * Get floor positions (horizontal heat map for a specific floor)
   * Normalizes X, Y accelerations to position within 1.5m x 1.5m car
   * 
   * @param {number} floor - Which floor to analyze
   * @returns {Array} Points with normalized (x, y) positions
   */
  getFloorHeatmap(floor) {
    const floorPoints = this.data.points.filter(p => {
      const detectedFloor = this.detectFloor(p.z);
      return detectedFloor === floor;
    });

    if (floorPoints.length === 0) return [];

    // Normalize to car dimensions (1.5m x 1.5m)
    const maxAccel = Math.max(...floorPoints.map(p => Math.max(Math.abs(p.x), Math.abs(p.y))));
    
    return floorPoints.map(p => ({
      ...p,
      // Normalize to 0-1.5m range (car size)
      normalizedX: (p.x / maxAccel) * (this.CAR_WIDTH / 2) + (this.CAR_WIDTH / 2),
      normalizedY: (p.y / maxAccel) * (this.CAR_DEPTH / 2) + (this.CAR_DEPTH / 2),
      // Intensity = time spent at this point
      intensity: Math.min(p.magnitude / 2, 1), // 0-1
    }));
  }

  /**
   * Get vertical heat map (which floors visited and duration)
   * Shows timeline of floor visits
   * 
   * @returns {Object} Floor visit data
   */
  getVerticalHeatmap() {
    const floorVisits = {};

    // Initialize all floors
    for (let i = 0; i <= 12; i++) {
      floorVisits[i] = {
        floor: i,
        floorName: this.getFloorName(i),
        duration: 0,
        visits: 0,
        lastVisit: null,
      };
    }

    // Count visits and duration per floor
    this.data.trajectory.forEach((visit, index) => {
      if (floorVisits[visit.floor]) {
        floorVisits[visit.floor].visits++;
        floorVisits[visit.floor].lastVisit = visit.timestamp;

        // Calculate duration until next floor change
        if (index < this.data.trajectory.length - 1) {
          const nextVisit = this.data.trajectory[index + 1];
          floorVisits[visit.floor].duration += (nextVisit.timestamp - visit.timestamp) / 1000; // seconds
        }
      }
    });

    return floorVisits;
  }

  /**
   * Get human-readable floor name
   * 0 = Car Top (machine room entry)
   * 1-12 = Individual floors
   */
  getFloorName(floor) {
    if (floor === 0) return 'Car Top (Machine Room)';
    if (floor >= 1 && floor <= 12) return `Floor ${floor}`;
    return 'Unknown';
  }

  /**
   * Analyze where technician spent most time
   * (Best for understanding where issue was fixed)
   * 
   * @returns {Array} Floors sorted by time spent
   */
  getWorkflowAnalysis() {
    const analysis = Object.values(this.getVerticalHeatmap())
      .filter(f => f.duration > 0)
      .sort((a, b) => b.duration - a.duration);

    return analysis;
  }

  /**
   * Generate report: Show path taken through elevator
   * Useful for understanding maintenance procedure
   * 
   * @returns {Array} Chronological path
   */
  getPath() {
    return this.data.trajectory.map((visit, index) => {
      const nextVisit = this.data.trajectory[index + 1];
      const duration = nextVisit 
        ? (nextVisit.timestamp - visit.timestamp) / 1000 
        : 0;

      return {
        order: index + 1,
        floor: visit.floor,
        floorName: this.getFloorName(visit.floor),
        time: new Date(visit.timestamp).toLocaleTimeString(),
        duration: Math.round(duration),
      };
    });
  }

  /**
   * Get summary statistics
   */
  getSummary() {
    return {
      totalPoints: this.data.points.length,
      totalFloors: this.data.trajectory.length,
      startFloor: this.data.trajectory[0]?.floor || 0,
      endFloor: this.data.trajectory[this.data.trajectory.length - 1]?.floor || 0,
      floorsVisited: new Set(this.data.trajectory.map(t => t.floor)).size,
      duration: this.data.duration,
    };
  }

  /**
   * Reset for new session
   */
  reset() {
    this.data = {
      points: [],
      floors: {},
      duration: 0,
      startTime: null,
      endTime: null,
      currentFloor: 0,
      trajectory: [],
    };
  }
}

export default HeatMapEngine;
