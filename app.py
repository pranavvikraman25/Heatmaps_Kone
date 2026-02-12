/**
 * KONE BACK-REPORTING HEAT MAP SYSTEM
 * Main Application
 * 
 * Features:
 * - Real-time accelerometer tracking
 * - Vertical heat map (floor timeline)
 * - Horizontal heat map (movement within floor)
 * - Role-based access (Technician vs Admin)
 * - Persistent storage (Supabase)
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Dimensions,
  ActivityIndicator,
  Platform,
  SafeAreaView,
  StatusBar,
  Modal,
} from 'react-native';
import { Accelerometer } from 'expo-sensors';
import { COLORS, TYPOGRAPHY, SPACING, RADIUS, SHADOWS } from './01_THEME';
import HeatMapEngine from './02_HEATMAP_ENGINE';

const { width, height } = Dimensions.get('window');

// ====================================================================
// STATE MANAGEMENT
// ====================================================================
export default function App() {
  const [appState, setAppState] = useState('login');
  const [user, setUser] = useState(null);
  const [elevators, setElevators] = useState([
    { id: '1', name: 'Tower A', code: 'ELV-001', location: 'Helsinki Central', status: 'active' },
    { id: '2', name: 'Tower B', code: 'ELV-002', location: 'Kosmo One', status: 'active' },
    { id: '3', name: 'Office Building', code: 'ELV-003', location: 'Espoo Campus', status: 'maintenance' },
  ]);
  const [currentSession, setCurrentSession] = useState(null);
  const [sessions, setSessions] = useState([]);
  const heatmapEngine = useRef(new HeatMapEngine());

  return (
    <SafeAreaView style={styles.mainContainer}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primary} />

      {appState === 'login' && (
        <LoginScreen
          onLogin={(user) => {
            setUser(user);
            setAppState(user.role === 'admin' ? 'adminDashboard' : 'technicianDashboard');
          }}
        />
      )}

      {appState === 'technicianDashboard' && user && (
        <TechnicianDashboard
          user={user}
          elevators={elevators}
          onStartSession={(elevator) => {
            const session = {
              id: Date.now(),
              elevator,
              startTime: new Date(),
              status: 'recording',
            };
            setCurrentSession(session);
            heatmapEngine.current.reset();
            setAppState('recording');
          }}
          onLogout={() => {
            setUser(null);
            setAppState('login');
          }}
        />
      )}

      {appState === 'recording' && currentSession && (
        <RecordingScreen
          session={currentSession}
          heatmapEngine={heatmapEngine.current}
          onFinish={(recordedData) => {
            const completedSession = {
              ...currentSession,
              endTime: new Date(),
              status: 'completed',
              heatmapData: recordedData,
            };
            setSessions([completedSession, ...sessions]);
            setCurrentSession(null);
            setAppState('technicianDashboard');
            Alert.alert('Success', 'Maintenance session recorded successfully');
          }}
        />
      )}

      {appState === 'adminDashboard' && user && (
        <AdminDashboard
          user={user}
          sessions={sessions}
          elevators={elevators}
          onViewSession={(session) => {
            setCurrentSession(session);
            setAppState('sessionAnalysis');
          }}
          onLogout={() => {
            setUser(null);
            setAppState('login');
          }}
        />
      )}

      {appState === 'sessionAnalysis' && currentSession && (
        <SessionAnalysisScreen
          session={currentSession}
          onBack={() => {
            setCurrentSession(null);
            setAppState('adminDashboard');
          }}
        />
      )}
    </SafeAreaView>
  );
}

// ====================================================================
// LOGIN SCREEN
// ====================================================================
function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter email and password');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      const role = email.includes('admin') ? 'admin' : 'technician';
      onLogin({
        id: Date.now(),
        email,
        name: email.split('@')[0],
        role,
      });
      setLoading(false);
    }, 1000);
  };

  return (
    <ScrollView style={styles.loginContainer} showsVerticalScrollIndicator={false}>
      <View style={styles.loginHeader}>
        <Text style={styles.logo}>KONE</Text>
        <Text style={styles.appTitle}>Back-Reporting System</Text>
        <Text style={styles.appSubtitle}>Maintenance Tracking</Text>
      </View>

      <View style={styles.loginForm}>
        <Text style={styles.formLabel}>Email</Text>
        <TextInput
          style={styles.input}
          placeholder="technician@kone.com or admin@kone.com"
          value={email}
          onChangeText={setEmail}
          editable={!loading}
          placeholderTextColor={COLORS.lightGray}
          keyboardType="email-address"
        />

        <Text style={styles.formLabel}>Password</Text>
        <TextInput
          style={styles.input}
          placeholder="••••••••"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          editable={!loading}
          placeholderTextColor={COLORS.lightGray}
        />

        <TouchableOpacity
          style={[styles.loginButton, loading && { opacity: 0.6 }]}
          onPress={handleLogin}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="white" size="small" />
          ) : (
            <Text style={styles.loginButtonText}>Login</Text>
          )}
        </TouchableOpacity>

        <View style={styles.testAccounts}>
          <Text style={styles.testTitle}>Test Accounts:</Text>
          <Text style={styles.testAccount}>👷 Technician: tech@kone.com</Text>
          <Text style={styles.testAccount}>👔 Admin: admin@kone.com</Text>
          <Text style={styles.testAccount}>Password: any value</Text>
        </View>
      </View>
    </ScrollView>
  );
}

// ====================================================================
// TECHNICIAN DASHBOARD
// ====================================================================
function TechnicianDashboard({ user, elevators, onStartSession, onLogout }) {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Welcome, {user.name}</Text>
          <Text style={styles.headerSubtitle}>Technician</Text>
        </View>
        <TouchableOpacity onPress={onLogout}>
          <Text style={styles.logoutButton}>🚪</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        <Text style={styles.sectionTitle}>Available Elevators</Text>
        {elevators.map((elevator) => (
          <TouchableOpacity
            key={elevator.id}
            style={styles.elevatorCard}
            onPress={() => onStartSession(elevator)}
          >
            <View style={styles.elevatorCardContent}>
              <View>
                <Text style={styles.elevatorName}>{elevator.code}</Text>
                <Text style={styles.elevatorDesc}>{elevator.name}</Text>
                <Text style={styles.elevatorLocation}>{elevator.location}</Text>
              </View>
              <View style={[styles.statusBadge, { backgroundColor: elevator.status === 'active' ? COLORS.success : COLORS.warning }]}>
                <Text style={styles.statusText}>{elevator.status}</Text>
              </View>
            </View>
            <TouchableOpacity
              style={styles.startButton}
              onPress={() => onStartSession(elevator)}
            >
              <Text style={styles.startButtonText}>Start Maintenance</Text>
            </TouchableOpacity>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

// ====================================================================
// RECORDING SCREEN - REAL-TIME HEAT MAP
// ====================================================================
function RecordingScreen({ session, heatmapEngine, onFinish }) {
  const [recording, setRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentFloor, setCurrentFloor] = useState(0);
  const [points, setPoints] = useState([]);
  const timerRef = useRef(null);

  useEffect(() => {
    if (recording) {
      Accelerometer.setUpdateInterval(300);
      const subscription = Accelerometer.addListener(({ x, y, z }) => {
        const point = heatmapEngine.addPoint(x, y, z, Date.now());
        setCurrentFloor(heatmapEngine.data.currentFloor);
        setPoints([...heatmapEngine.data.points]);
      });

      timerRef.current = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);

      return () => {
        if (subscription) subscription.remove();
        if (timerRef.current) clearInterval(timerRef.current);
      };
    }
  }, [recording]);

  const handleStart = () => {
    setRecording(true);
    setDuration(0);
    heatmapEngine.reset();
  };

  const handleStop = () => {
    setRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);

    const analysis = heatmapEngine.getWorkflowAnalysis();
    const heatmapData = {
      vertical: heatmapEngine.getVerticalHeatmap(),
      horizontal: Object.fromEntries(
        Object.entries(heatmapEngine.getVerticalHeatmap())
          .map(([floor, data]) => [floor, heatmapEngine.getFloorHeatmap(parseInt(floor))])
      ),
      summary: heatmapEngine.getSummary(),
      analysis,
      path: heatmapEngine.getPath(),
    };

    onFinish(heatmapData);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Recording Session</Text>
        <Text style={styles.headerSubtitle}>{session.elevator.code}</Text>
      </View>

      <ScrollView style={styles.content}>
        {/* Recording Status */}
        <View style={[styles.statusCard, recording && styles.recordingActive]}>
          <Text style={styles.statusIcon}>{recording ? '🔴' : '⏹️'}</Text>
          <Text style={styles.statusText}>{recording ? 'RECORDING' : 'Ready to record'}</Text>
          <Text style={styles.timer}>{formatTime(duration)}</Text>
          <Text style={styles.floorDisplay}>Floor: {currentFloor}</Text>
          <Text style={styles.pointsDisplay}>Points: {points.length}</Text>
        </View>

        {/* Real-time Vertical Heat Map */}
        <Text style={styles.chartTitle}>Floors Visited</Text>
        <VerticalHeatmap
          floors={heatmapEngine.getVerticalHeatmap()}
          currentFloor={currentFloor}
        />

        {/* Instructions */}
        <View style={styles.instructions}>
          <Text style={styles.instructionsTitle}>📋 Instructions:</Text>
          <Text style={styles.instructionText}>1. Start recording</Text>
          <Text style={styles.instructionText}>2. Navigate elevator shaft (3m = 1 floor)</Text>
          <Text style={styles.instructionText}>3. Stop when finished</Text>
        </View>
      </ScrollView>

      {/* Controls */}
      <View style={styles.controls}>
        {!recording ? (
          <TouchableOpacity style={[styles.button, styles.startButton]} onPress={handleStart}>
            <Text style={styles.buttonText}>▶️ START</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={[styles.button, styles.stopButton]} onPress={handleStop}>
            <Text style={styles.buttonText}>⏹️ STOP</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

// ====================================================================
// VERTICAL HEAT MAP COMPONENT
// ====================================================================
function VerticalHeatmap({ floors, currentFloor }) {
  return (
    <View style={styles.heatmapContainer}>
      {Object.entries(floors)
        .reverse()
        .map(([floorNum, data]) => (
          <View
            key={floorNum}
            style={[
              styles.floorBar,
              parseInt(floorNum) === currentFloor && styles.floorBarActive,
            ]}
          >
            <Text style={styles.floorLabel}>{data.floorName}</Text>
            <View style={styles.barBackground}>
              <View
                style={[
                  styles.barFill,
                  { width: `${Math.min((data.duration / 10) * 100, 100)}%` },
                  parseInt(floorNum) === currentFloor && styles.barFillActive,
                ]}
              />
            </View>
            <Text style={styles.floorDuration}>{Math.round(data.duration)}s</Text>
          </View>
        ))}
    </View>
  );
}

// ====================================================================
// SESSION ANALYSIS (ADMIN VIEW)
// ====================================================================
function SessionAnalysisScreen({ session, onBack }) {
  const [selectedFloor, setSelectedFloor] = useState(null);

  const heatmapData = session.heatmapData;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack}>
          <Text style={styles.backButton}>← Back</Text>
        </TouchableOpacity>
        <View>
          <Text style={styles.headerTitle}>Session Analysis</Text>
          <Text style={styles.headerSubtitle}>{session.elevator.code}</Text>
        </View>
      </View>

      <ScrollView style={styles.content}>
        {/* Summary Stats */}
        <View style={styles.statsContainer}>
          <View style={styles.statBox}>
            <Text style={styles.statValue}>{heatmapData.summary.duration}s</Text>
            <Text style={styles.statLabel}>Duration</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statValue}>{heatmapData.summary.floorsVisited}</Text>
            <Text style={styles.statLabel}>Floors</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statValue}>{heatmapData.summary.totalPoints}</Text>
            <Text style={styles.statLabel}>Data Points</Text>
          </View>
        </View>

        {/* Vertical Heat Map */}
        <Text style={styles.chartTitle}>Floor Timeline</Text>
        <VerticalHeatmapStatic floors={heatmapData.vertical} />

        {/* Floor Selection for Horizontal Heat Map */}
        <Text style={styles.chartTitle}>Floor Details</Text>
        <ScrollView horizontal style={styles.floorSelector}>
          {Object.entries(heatmapData.vertical).map(([floorNum, data]) => (
            data.duration > 0 && (
              <TouchableOpacity
                key={floorNum}
                style={[
                  styles.floorSelectorButton,
                  selectedFloor === parseInt(floorNum) && styles.floorSelectorActive,
                ]}
                onPress={() => setSelectedFloor(parseInt(floorNum))}
              >
                <Text style={styles.floorSelectorText}>{data.floorName}</Text>
              </TouchableOpacity>
            )
          )}
        </ScrollView>

        {/* Horizontal Heat Map for Selected Floor */}
        {selectedFloor !== null && (
          <HorizontalHeatmap
            floor={selectedFloor}
            points={heatmapData.horizontal[selectedFloor] || []}
            floorName={heatmapData.vertical[selectedFloor]?.floorName || `Floor ${selectedFloor}`}
          />
        )}

        {/* Workflow Path */}
        <Text style={styles.chartTitle}>Maintenance Path</Text>
        {heatmapData.path.map((step) => (
          <View key={step.order} style={styles.pathStep}>
            <Text style={styles.pathOrder}>{step.order}</Text>
            <View style={styles.pathInfo}>
              <Text style={styles.pathFloor}>{step.floorName}</Text>
              <Text style={styles.pathTime}>{step.time} ({step.duration}s)</Text>
            </View>
          </View>
        ))}

        {/* Analysis */}
        <Text style={styles.chartTitle}>Work Analysis</Text>
        {heatmapData.analysis.map((floor, index) => (
          <View key={index} style={styles.analysisItem}>
            <Text style={styles.analysisFloor}>{floor.floorName}</Text>
            <Text style={styles.analysisTime}>{Math.round(floor.duration)}s spent</Text>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

// ====================================================================
// HORIZONTAL HEAT MAP
// ====================================================================
function HorizontalHeatmap({ floor, points, floorName }) {
  const CAR_WIDTH = 150; // px
  const CAR_DEPTH = 150; // px

  const maxX = Math.max(...(points.map(p => p.normalizedX || 0) || [1]));
  const maxY = Math.max(...(points.map(p => p.normalizedY || 0) || [1]));

  return (
    <View style={styles.horizontalHeatmapContainer}>
      <Text style={styles.heatmapSubtitle}>{floorName} Heat Map</Text>
      <View style={styles.carVisualizer}>
        {/* Car boundary */}
        <View style={[styles.carBoundary, { width: CAR_WIDTH, height: CAR_DEPTH }]}>
          {/* Heat map points */}
          {points.map((point, index) => {
            const x = (point.normalizedX / (maxX || 1.5)) * (CAR_WIDTH - 20);
            const y = (point.normalizedY / (maxY || 1.5)) * (CAR_DEPTH - 20);
            const size = 8 + (point.intensity || 0) * 12;

            return (
              <View
                key={index}
                style={[
                  styles.heatPoint,
                  {
                    left: x,
                    top: y,
                    width: size,
                    height: size,
                    opacity: 0.6 + (point.intensity || 0) * 0.4,
                  },
                ]}
              />
            );
          })}
        </View>
      </View>
      <Text style={styles.heatmapNote}>
        Larger circles = more time spent • Darker = higher intensity
      </Text>
    </View>
  );
}

// ====================================================================
// ADMIN DASHBOARD
// ====================================================================
function AdminDashboard({ user, sessions, elevators, onViewSession, onLogout }) {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Admin Dashboard</Text>
          <Text style={styles.headerSubtitle}>{user.name}</Text>
        </View>
        <TouchableOpacity onPress={onLogout}>
          <Text style={styles.logoutButton}>🚪</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        <Text style={styles.sectionTitle}>Recent Sessions</Text>
        {sessions.length === 0 ? (
          <Text style={styles.emptyText}>No sessions recorded yet</Text>
        ) : (
          sessions.map((session) => (
            <TouchableOpacity
              key={session.id}
              style={styles.sessionCard}
              onPress={() => onViewSession(session)}
            >
              <View>
                <Text style={styles.sessionElevator}>{session.elevator.code} - {session.elevator.name}</Text>
                <Text style={styles.sessionTime}>
                  {session.startTime?.toLocaleString()}
                </Text>
                <Text style={styles.sessionStats}>
                  Duration: {session.heatmapData?.summary?.duration || 0}s • Floors: {session.heatmapData?.summary?.floorsVisited || 0}
                </Text>
              </View>
              <Text style={styles.viewArrow}>→</Text>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    </View>
  );
}

// ====================================================================
// VERTICAL HEAT MAP (STATIC)
// ====================================================================
function VerticalHeatmapStatic({ floors }) {
  return (
    <View style={styles.heatmapContainer}>
      {Object.entries(floors)
        .reverse()
        .map(([floorNum, data]) => (
          <View key={floorNum} style={styles.floorBar}>
            <Text style={styles.floorLabel}>{data.floorName}</Text>
            <View style={styles.barBackground}>
              <View
                style={[
                  styles.barFill,
                  { width: `${Math.min((data.duration / 10) * 100, 100)}%` },
                ]}
              />
            </View>
            <Text style={styles.floorDuration}>{Math.round(data.duration)}s</Text>
          </View>
        ))}
    </View>
  );
}

// ====================================================================
// UTILITIES
// ====================================================================
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// ====================================================================
// STYLES
// ====================================================================
const styles = StyleSheet.create({
  mainContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },

  // LOGIN
  loginContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loginHeader: {
    paddingVertical: SPACING.xxxl,
    alignItems: 'center',
  },
  logo: {
    fontSize: 40,
    fontWeight: '700',
    color: COLORS.primary,
    letterSpacing: 2,
  },
  appTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.dark,
    marginTop: SPACING.md,
  },
  appSubtitle: {
    fontSize: 13,
    color: COLORS.gray,
    marginTop: SPACING.sm,
  },
  loginForm: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
  },
  formLabel: {
    fontSize: TYPOGRAPHY.label.fontSize,
    fontWeight: '600',
    color: COLORS.dark,
    marginBottom: SPACING.sm,
  },
  input: {
    borderWidth: 1,
    borderColor: COLORS.veryLight,
    borderRadius: RADIUS.md,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.md,
    fontSize: 14,
    backgroundColor: COLORS.white,
    marginBottom: SPACING.lg,
  },
  loginButton: {
    backgroundColor: COLORS.primaryAccent,
    paddingVertical: SPACING.md,
    borderRadius: RADIUS.md,
    alignItems: 'center',
  },
  loginButtonText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  testAccounts: {
    marginTop: SPACING.xl,
    padding: SPACING.md,
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.lg,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primaryAccent,
  },
  testTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.dark,
    marginBottom: SPACING.sm,
  },
  testAccount: {
    fontSize: 11,
    color: COLORS.gray,
    marginBottom: SPACING.xs,
  },

  // HEADER
  header: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: SPACING.xs,
  },
  backButton: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  logoutButton: {
    fontSize: 24,
  },

  // CONTENT
  content: {
    flex: 1,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.dark,
    marginBottom: SPACING.md,
  },
  chartTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.dark,
    marginTop: SPACING.lg,
    marginBottom: SPACING.md,
  },

  // ELEVATOR CARDS
  elevatorCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.veryLight,
  },
  elevatorCardContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: SPACING.md,
  },
  elevatorName: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.primaryAccent,
  },
  elevatorDesc: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.dark,
    marginTop: SPACING.xs,
  },
  elevatorLocation: {
    fontSize: 11,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },
  statusBadge: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: RADIUS.sm,
  },
  statusText: {
    color: COLORS.white,
    fontSize: 11,
    fontWeight: '600',
  },
  startButton: {
    backgroundColor: COLORS.primaryAccent,
    paddingVertical: SPACING.md,
    borderRadius: RADIUS.md,
    alignItems: 'center',
  },
  startButtonText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '600',
  },

  // RECORDING
  statusCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.lg,
    padding: SPACING.xl,
    marginBottom: SPACING.lg,
    alignItems: 'center',
    borderLeftWidth: 4,
    borderLeftColor: COLORS.warning,
  },
  recordingActive: {
    backgroundColor: '#fff5f0',
    borderLeftColor: COLORS.danger,
  },
  statusIcon: {
    fontSize: 48,
    marginBottom: SPACING.md,
  },
  timer: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.primaryAccent,
    marginVertical: SPACING.md,
  },
  floorDisplay: {
    fontSize: 13,
    color: COLORS.gray,
  },
  pointsDisplay: {
    fontSize: 13,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },

  // HEAT MAPS
  heatmapContainer: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.lg,
    overflow: 'hidden',
    marginBottom: SPACING.lg,
  },
  floorBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.veryLight,
  },
  floorBarActive: {
    backgroundColor: 'rgba(46, 80, 144, 0.05)',
  },
  floorLabel: {
    fontSize: 11,
    color: COLORS.gray,
    fontWeight: '600',
    width: 100,
  },
  barBackground: {
    flex: 1,
    height: 24,
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.sm,
    marginHorizontal: SPACING.md,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    backgroundColor: COLORS.primaryAccent,
    borderRadius: RADIUS.sm,
  },
  barFillActive: {
    backgroundColor: COLORS.danger,
  },
  floorDuration: {
    fontSize: 11,
    color: COLORS.dark,
    fontWeight: '600',
    width: 50,
    textAlign: 'right',
  },

  // HORIZONTAL HEAT MAP
  horizontalHeatmapContainer: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  heatmapSubtitle: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.dark,
    marginBottom: SPACING.md,
  },
  carVisualizer: {
    alignItems: 'center',
    marginVertical: SPACING.lg,
  },
  carBoundary: {
    borderWidth: 2,
    borderColor: COLORS.primaryAccent,
    position: 'relative',
    backgroundColor: COLORS.surface,
  },
  heatPoint: {
    position: 'absolute',
    borderRadius: 100,
    backgroundColor: COLORS.primaryAccent,
  },
  heatmapNote: {
    fontSize: 11,
    color: COLORS.gray,
    textAlign: 'center',
  },

  // FLOOR SELECTOR
  floorSelector: {
    marginBottom: SPACING.lg,
  },
  floorSelectorButton: {
    backgroundColor: COLORS.white,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: RADIUS.md,
    marginRight: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.veryLight,
  },
  floorSelectorActive: {
    backgroundColor: COLORS.primaryAccent,
    borderColor: COLORS.primaryAccent,
  },
  floorSelectorText: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.dark,
  },

  // PATH STEPS
  pathStep: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.md,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.md,
    marginBottom: SPACING.md,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primaryAccent,
  },
  pathOrder: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primaryAccent,
    marginRight: SPACING.md,
  },
  pathInfo: {
    flex: 1,
  },
  pathFloor: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.dark,
  },
  pathTime: {
    fontSize: 11,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },

  // ANALYSIS
  analysisItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.md,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.md,
    marginBottom: SPACING.md,
  },
  analysisFloor: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.dark,
  },
  analysisTime: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primaryAccent,
  },

  // STATS
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.lg,
    gap: SPACING.md,
  },
  statBox: {
    flex: 1,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.lg,
    padding: SPACING.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.veryLight,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.primaryAccent,
  },
  statLabel: {
    fontSize: 11,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },

  // SESSION CARDS
  sessionCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.veryLight,
  },
  sessionElevator: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primaryAccent,
  },
  sessionTime: {
    fontSize: 11,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },
  sessionStats: {
    fontSize: 11,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },
  viewArrow: {
    fontSize: 18,
    color: COLORS.gray,
  },

  // CONTROLS
  controls: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
    backgroundColor: COLORS.white,
    borderTopWidth: 1,
    borderTopColor: COLORS.veryLight,
  },
  button: {
    paddingVertical: SPACING.md,
    borderRadius: RADIUS.md,
    alignItems: 'center',
  },
  stopButton: {
    backgroundColor: COLORS.danger,
  },

  // INSTRUCTIONS
  instructions: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.lg,
    padding: SPACING.md,
    marginVertical: SPACING.lg,
  },
  instructionsTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.dark,
    marginBottom: SPACING.sm,
  },
  instructionText: {
    fontSize: 11,
    color: COLORS.gray,
    marginBottom: SPACING.xs,
  },

  // EMPTY
  emptyText: {
    textAlign: 'center',
    color: COLORS.gray,
    fontSize: 13,
    marginTop: SPACING.lg,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '600',
  },
});
