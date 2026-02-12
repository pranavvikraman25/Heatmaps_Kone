/**
 * SUPABASE DATABASE SCHEMA
 * 
 * SQL statements to create tables for KONE Back-Reporting System
 * Run these in Supabase SQL Editor
 */

export const SQL_SCHEMA = `
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL CHECK (role IN ('technician', 'admin')),
  status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Elevators table
CREATE TABLE elevators (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  elevator_id VARCHAR(20) UNIQUE NOT NULL,  -- ELV-001, ELV-002, etc
  name VARCHAR(255) NOT NULL,                -- Tower A, Tower B, etc
  location VARCHAR(255) NOT NULL,
  total_floors INTEGER NOT NULL DEFAULT 12,
  car_width DECIMAL(5,2) DEFAULT 1.5,      -- 1.5 meters
  car_depth DECIMAL(5,2) DEFAULT 1.5,
  floor_height DECIMAL(5,2) DEFAULT 3,     -- 3 meters per floor
  status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'inactive')),
  last_maintenance TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Maintenance sessions table
CREATE TABLE maintenance_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  elevator_id UUID NOT NULL REFERENCES elevators(id),
  technician_id UUID NOT NULL REFERENCES users(id),
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP,
  status VARCHAR(50) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'cancelled')),
  duration_seconds INTEGER,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Accelerometer data points table
CREATE TABLE accelerometer_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES maintenance_sessions(id) ON DELETE CASCADE,
  x DECIMAL(10,4) NOT NULL,  -- X acceleration
  y DECIMAL(10,4) NOT NULL,  -- Y acceleration
  z DECIMAL(10,4) NOT NULL,  -- Z acceleration (vertical)
  magnitude DECIMAL(10,4),   -- Computed magnitude
  recorded_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Floor visits table (derived from accelerometer data)
CREATE TABLE floor_visits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES maintenance_sessions(id) ON DELETE CASCADE,
  floor_number INTEGER NOT NULL CHECK (floor_number >= 0 AND floor_number <= 12),
  enter_time TIMESTAMP NOT NULL,
  exit_time TIMESTAMP,
  duration_seconds INTEGER,
  work_intensity DECIMAL(3,2),  -- 0-1 scale
  points_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Heat map snapshots (cached for performance)
CREATE TABLE heatmap_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES maintenance_sessions(id) ON DELETE CASCADE,
  floor_number INTEGER NOT NULL,
  heatmap_data JSONB NOT NULL,  -- Contains normalized x,y,intensity points
  created_at TIMESTAMP DEFAULT NOW()
);

-- Issues/Faults table
CREATE TABLE issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  elevator_id UUID NOT NULL REFERENCES elevators(id),
  fault_code VARCHAR(20) NOT NULL,
  description TEXT NOT NULL,
  severity VARCHAR(50) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
  status VARCHAR(50) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
  reported_at TIMESTAMP NOT NULL,
  resolved_at TIMESTAMP,
  resolved_by UUID REFERENCES users(id),
  resolution_notes TEXT,
  session_id UUID REFERENCES maintenance_sessions(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Activity log (for audit trail)
CREATE TABLE activity_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  action VARCHAR(255) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,  -- 'session', 'elevator', 'issue', etc
  entity_id UUID,
  details JSONB,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_sessions_elevator ON maintenance_sessions(elevator_id);
CREATE INDEX idx_sessions_technician ON maintenance_sessions(technician_id);
CREATE INDEX idx_sessions_status ON maintenance_sessions(status);
CREATE INDEX idx_accelerometer_session ON accelerometer_data(session_id);
CREATE INDEX idx_accelerometer_time ON accelerometer_data(recorded_at);
CREATE INDEX idx_floor_visits_session ON floor_visits(session_id);
CREATE INDEX idx_floor_visits_floor ON floor_visits(floor_number);
CREATE INDEX idx_issues_elevator ON issues(elevator_id);
CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_activity_user ON activity_log(user_id);
CREATE INDEX idx_activity_timestamp ON activity_log(timestamp);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE accelerometer_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE floor_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can only see their own data + admins see all
CREATE POLICY "Users see own data" ON users 
FOR SELECT USING (auth.uid() = id OR auth.jwt() ->> 'role' = 'admin');

-- Technicians see own sessions, admins see all
CREATE POLICY "Sessions visibility" ON maintenance_sessions 
FOR SELECT USING (
  technician_id = auth.uid() OR 
  auth.jwt() ->> 'role' = 'admin'
);

-- Technicians can insert own accelerometer data, admins can view all
CREATE POLICY "Accelerometer insert" ON accelerometer_data 
FOR INSERT WITH CHECK (
  EXISTS (
    SELECT 1 FROM maintenance_sessions 
    WHERE id = session_id AND technician_id = auth.uid()
  )
);

CREATE POLICY "Accelerometer select" ON accelerometer_data 
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM maintenance_sessions ms 
    WHERE ms.id = session_id AND (
      ms.technician_id = auth.uid() OR 
      auth.jwt() ->> 'role' = 'admin'
    )
  )
);
`;

/**
 * Database queries
 */
export const QUERIES = {
  // Create new maintenance session
  createSession: (elevatorId, technicianId) => `
    INSERT INTO maintenance_sessions (elevator_id, technician_id, start_time, status)
    VALUES ('${elevatorId}', '${technicianId}', NOW(), 'in_progress')
    RETURNING *;
  `,

  // Get active session for technician
  getActiveSession: (technicianId) => `
    SELECT * FROM maintenance_sessions 
    WHERE technician_id = '${technicianId}' AND status = 'in_progress'
    ORDER BY start_time DESC LIMIT 1;
  `,

  // Insert accelerometer data point
  insertAccelerometerData: (sessionId, x, y, z, magnitude) => `
    INSERT INTO accelerometer_data (session_id, x, y, z, magnitude, recorded_at)
    VALUES ('${sessionId}', ${x}, ${y}, ${z}, ${magnitude}, NOW())
    RETURNING *;
  `,

  // Get all data for a session
  getSessionData: (sessionId) => `
    SELECT * FROM accelerometer_data 
    WHERE session_id = '${sessionId}'
    ORDER BY recorded_at ASC;
  `,

  // Create floor visit
  insertFloorVisit: (sessionId, floor, enterTime) => `
    INSERT INTO floor_visits (session_id, floor_number, enter_time)
    VALUES ('${sessionId}', ${floor}, '${enterTime}')
    RETURNING *;
  `,

  // Update floor visit with exit time
  updateFloorVisit: (visitId, exitTime, duration, intensity) => `
    UPDATE floor_visits 
    SET exit_time = '${exitTime}', 
        duration_seconds = ${duration},
        work_intensity = ${intensity}
    WHERE id = '${visitId}'
    RETURNING *;
  `,

  // Get floor visits for session
  getFloorVisits: (sessionId) => `
    SELECT * FROM floor_visits 
    WHERE session_id = '${sessionId}'
    ORDER BY enter_time ASC;
  `,

  // Get all issues for elevator
  getElevatorIssues: (elevatorId) => `
    SELECT * FROM issues 
    WHERE elevator_id = '${elevatorId}' AND status != 'closed'
    ORDER BY reported_at DESC;
  `,

  // Resolve issue with session reference
  resolveIssue: (issueId, sessionId, notes) => `
    UPDATE issues 
    SET status = 'resolved',
        resolved_at = NOW(),
        session_id = '${sessionId}',
        resolution_notes = '${notes}'
    WHERE id = '${issueId}'
    RETURNING *;
  `,

  // Get technician's recent sessions
  getTechnicianSessions: (technicianId, limit = 10) => `
    SELECT * FROM maintenance_sessions 
    WHERE technician_id = '${technicianId}'
    ORDER BY start_time DESC
    LIMIT ${limit};
  `,

  // Admin: Get all sessions
  getAllSessions: () => `
    SELECT 
      ms.*,
      u.name as technician_name,
      e.elevator_id,
      e.name as elevator_name
    FROM maintenance_sessions ms
    JOIN users u ON ms.technician_id = u.id
    JOIN elevators e ON ms.elevator_id = e.id
    ORDER BY ms.start_time DESC;
  `,

  // Admin: Get session with full heat map data
  getSessionWithHeatmap: (sessionId) => `
    SELECT 
      ms.*,
      u.name as technician_name,
      e.elevator_id,
      e.name as elevator_name,
      COALESCE(
        json_agg(json_build_object(
          'id', fv.id,
          'floor', fv.floor_number,
          'duration', fv.duration_seconds,
          'intensity', fv.work_intensity,
          'enter_time', fv.enter_time,
          'exit_time', fv.exit_time
        )) FILTER (WHERE fv.id IS NOT NULL),
        '[]'::json
      ) as floor_visits
    FROM maintenance_sessions ms
    JOIN users u ON ms.technician_id = u.id
    JOIN elevators e ON ms.elevator_id = e.id
    LEFT JOIN floor_visits fv ON ms.id = fv.session_id
    WHERE ms.id = '${sessionId}'
    GROUP BY ms.id, u.id, e.id;
  `,

  // Log activity
  logActivity: (userId, action, entityType, entityId, details) => `
    INSERT INTO activity_log (user_id, action, entity_type, entity_id, details)
    VALUES ('${userId}', '${action}', '${entityType}', '${entityId}', '${JSON.stringify(details)}')
    RETURNING *;
  `,
};

export default { SQL_SCHEMA, QUERIES };
