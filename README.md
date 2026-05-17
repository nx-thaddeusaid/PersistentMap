# PersistentMap

Server and in-game client for the RogueTech persistent war map. The server tracks star system ownership and mission results across all players; the client mod reports mission outcomes from inside the game and displays the current war state on the in-game galaxy map.

**Upstream repo:** [Morphyum/PersistentMap](https://github.com/Morphyum/PersistentMap)  
**Live map:** [roguewar.org](http://roguewar.org)

---

## Repository structure

```
PersistentMapAPI/       — Shared data types and service contracts (used by server and client)
PersistentMapServer/    — ASP.NET WCF REST server; tracks system ownership and mission results
PersistentMapClient/    — ModTek mod (C#); reports results and fetches map state in-game
DataGenerator/          — Utility for seeding the server's initial star system data
```

---

## Building

### Requirements

- Visual Studio 2017+ (Community edition works) with **.NET desktop development** workload
- BattleTech game install (for the client mod's game DLL references)

### Server

```bash
cd PersistentMapServer
# Restore NuGet packages, then:
dotnet build --configuration Release
```

Before running, configure the service binding:

```bash
# Allow localhost:8001 binding (Windows — run as admin)
netsh http add urlacl url=http://+:8001/warServices user=<USERNAME>
```

### Client (ModTek mod)

```bash
cd PersistentMapClient
dotnet build --configuration Release -p:BattleTechGameDir="/path/to/BATTLETECH"
```

Add a reference to the relevant BattleTech managed DLLs from:
```
<game>/BattleTech_Data/Managed/
```

---

## Server configuration

The server URL is set in the client mod's `mod.json` settings:

```json
"ServerURL": "http://roguewar.org:8001/"
```

For local development, point this at `http://localhost:8001/`.

---

## Data seeding

The `DataGenerator/` tool generates the initial star system dataset from `InnerSphereMap` data. Run it once before starting a fresh server instance.
