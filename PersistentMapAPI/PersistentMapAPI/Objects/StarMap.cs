using System;
using System.Collections.Generic;
using System.Linq;
using PersistentMapAPI.Objects;

namespace PersistentMapAPI {
    public class StarMap : ICloneable {

        public List<System> systems = new List<System>();

        public System FindSystemByName(string name) {
            System result = null;
            if (systems != null && systems.Count > 0) {
                result = systems.FirstOrDefault(x => x.name.Equals(name));
            }
            return result;
        }

        // Deep clone — copies systems list and each system's controlList and companies
        // so callers can read without racing against concurrent PostMissionResult mutations.
        public object Clone() {
            var cloned = (StarMap)MemberwiseClone();
            cloned.systems = systems?.Select(s => new System {
                name = s.name,
                activePlayers = s.activePlayers,
                controlList = s.controlList?.Select(fc => new FactionControl {
                    faction = fc.faction,
                    percentage = fc.percentage
                }).ToList() ?? new List<FactionControl>(),
                companies = s.companies?.Select(c => new Company {
                    Name = c.Name,
                    Faction = c.Faction
                }).ToList() ?? new List<Company>()
            }).ToList() ?? new List<System>();
            return cloned;
        }

    }
}
