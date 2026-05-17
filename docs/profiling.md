# PersistentMap — Performance Profiling

## Context

PersistentMapServer targets .NET Framework 4.7.1 with a classic WCF service host. Its hot paths are:

- `StarMapStateManager` — ownership recalculation called on every player action
- `PlayerStateManager` — player auth + action validation
- `FactionInventoryStateManager` — inventory state transitions
- `BackupWorker` — periodic serialisation to disk

Isolation via BenchmarkDotNet is not practical: the server classes depend on WCF service contracts and `PersistentMapAPI` types that reference System.ServiceModel. Use `dotnet-trace` against a running server instance instead.

---

## dotnet-trace Profiling (recommended)

### Prerequisites

```bash
dotnet tool install -g dotnet-trace
dotnet tool install -g dotnet-counters
```

### Step 1 — Start the server

```bash
cd PersistentMapServer/PersistentMapServer
dotnet run --configuration Release
```

Or launch via the existing IIS/service host. Note the process ID:

```bash
PID=$(pgrep -f PersistentMapServer)
```

### Step 2 — Seed load with DataGenerator

```bash
cd DataGenerator/DataGenerator
dotnet run --configuration Release -- --help
```

Run a sequence of player actions to put the server under realistic load before capturing.

### Step 3 — Capture a CPU profile

```bash
# 30-second CPU sampling profile
dotnet-trace collect --process-id $PID \
  --duration 00:00:30 \
  --profile cpu-sampling \
  --output persistentmap.nettrace
```

### Step 4 — Analyse

Open `persistentmap.nettrace` in one of:

- **PerfView** (Windows) — flame graphs, call trees, GC analysis
- **SpeedScope** (`speedscope.app`) — drag-and-drop, fast flame graph rendering
- **Visual Studio Diagnostic Tools** (if on Windows)

Filter the call tree to `PersistentMapServer.*` frames to isolate server logic from framework overhead.

---

## dotnet-counters — Live metrics

Use this for a quick real-time view without capturing a full trace:

```bash
dotnet-counters monitor --process-id $PID \
  --counters System.Runtime \
  --refresh-interval 2
```

Watch for:
- `gc-heap-size` growth over time (memory leak signals)
- `threadpool-queue-length` buildup (request saturation)
- `cpu-usage` spikes correlating with recalculation cycles

---

## Known hot paths to investigate first

| Class | Method | Why |
|---|---|---|
| `StarMapStateManager` | `UpdateControl` | Called on every valid player action; O(systems) scan |
| `PlayerStateManager` | `ValidateAction` | Auth + cooldown check on every request |
| `FactionInventoryStateManager` | `ApplyChange` | Inventory mutation under lock |
| `BackupWorker` | `DoBackup` | Full serialisation to disk on timer |

---

## GZip interceptor note

`PersistentMapServer/GZip/` contains a WCF message inspector that compresses responses. If profiling shows unusual CPU in the response path, check whether GZip is adding overhead for small payloads — disabling it for local profiling sessions is safe.
