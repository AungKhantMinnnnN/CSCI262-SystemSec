import sys
import math
import random 
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

# Data Structures
@dataclass
class Event:
    name: str
    eventType: str
    minVal: int
    maxVal: Optional[float]
    weight: int

@dataclass
class EventStats:
    name: str
    mean: float
    stdDev: float

# Helper functions
def readEvents(path: str) -> Dict[str, Event]:
    events: Dict[str, Event] = {}
    with open(path, 'r') as f:
        header = f.readline()
        if not header:
            raise ValueError("Empty event file")
        try:
            expectedCount = int(header.strip())
        except ValueError:
            raise ValueError("First line of Events.txt must be int.")
        lines = [line.strip() for line in f if line.strip()]
    
    if len(lines) != expectedCount:
        print(f"[WARN] Mismatch event count: header={expectedCount}, actual={len(lines)}")
    
    for line in lines:
        # Format: EventName:[C/D]:minimum:maximum:weight
        parts = line.split(":")
        if len(parts) < 5:
            raise ValueError(f"Invalid line in Events.txt: {line}")
        name = parts[0]
        eventType = parts[1].strip().upper()
        if eventType not in ("C", "D"):
            raise ValueError(f"Invalid event type '{eventType}' for event '{name}'")
        minValueStr = parts[2].strip()
        maxValueStr = parts[3].strip()
        weightStr = parts[4].strip()

        minValue = float(minValueStr) if minValueStr else 0.0
        maxValue: Optional[float] = float(maxValueStr) if maxValueStr else None
        weight = int(weightStr) if weightStr else 1

        events[name] = Event(
            name=name,
            eventType=eventType,
            minVal=minValue,
            maxVal=maxValue,
            weight=weight
        )

    print(f"[INFO] Loaded Events from {path} : {len(events)}")
    for event in events.values():
        print(f"{event}")
    
    return events

def readStats(path: str) -> Dict[str, EventStats]:
    stats: Dict[str, EventStats] = {}
    with open(path, "r") as f:
        header = f.readline()
        if not header:
            raise ValueError("Stats.txt file is empty")
        
        try:
            expectedCount = int(header.strip())
        except ValueError:
            raise ValueError("First line of Stats.txt must be int.")
        
        lines = [line.strip() for line in f if line.strip()]

        if len(lines) != expectedCount:
            print(f"[WARN] Mismatch stats count: header={header}, actual={len.lines}")

        for line in lines:
            # Format : EventName:mean:standardDeviation
            parts = line.split(":")
            if len(parts) < 3:
                raise ValueError(f"Invalid line in stats.txt file: {line}")
            name = parts[0]
            mean = float(parts[1])
            stdDev = float(parts[2])
            stats[name] = EventStats(name=name, mean=mean, stdDev=stdDev)
        
        print(f"[INFO] Loaded Stats from {path} : {len(stats)}")
        for stat in stats.values():
            print(f"{stat}")
        
    return stats

# Consistency check function
def check(events:Dict[str, Event], stats:Dict[str, EventStats]):
    checkSuccess = True

    # mismatch names
    for name in events:
        if name not in stats:
            print(f"[ERROR] Event '{name}' is in Events.txt but not in Stats.txt")
            checkSuccess = False
    
    for name in stats:
        if name not in events:
            print(f"[ERROR] Event '{name}' is in Stats.txt but not in Events.txt")
            checkSuccess = False

    # Range and mean/standard deviation/weight comparison
    for name, event in events.items():
        if name not in stats:
            continue

        stat = stats[name]

        # Mean between min/max
        if stat.mean < event.minVal:
            print(f"[WARN] Mean of '{name}' is lower than minimum value ({event.minVal})")
            checkSuccess = False
        if event.maxVal is not None and stat.mean > event.maxVal:
            print(f"[WARN] Mean of '{name}' is higher than maximum value ({event.maxVal})")
            checkSuccess = False

        if stat.stdDev <= 0:
            print(f"[WARN] Standard deviation of '{name}' is 0 or non positive ({stat.stdDev})")
            checkSuccess = False
        
        if event.weight <= 0:
            print(f"[WARN] Weight of '{name}' is 0 or non positive ({event.weight})")
            checkSuccess = False

    if checkSuccess:
        print("[INFO] No inconsisties within Events.txt and Stats.txt detected.")
    else:
        print("[INFO] Inconsisties were detectd. Review the above log messages.")
    
    return checkSuccess

# Activity engine
def valueGenerator(event: Event, stats: EventStats) -> float:
    # Generate a single day's total for an event.
    value = random.gauss(stats.mean, stats.stdDev)

    if value < event.minVal:
        value = event.minVal
    if event.maxVal is not None and value > event.maxVal:
        value = event.maxVal
    
    if event.eventType == "D":
        value = round(value)
        if value < event.minVal:
            value = event.minVal
        if value < 0:
            value = 0
    else:
        value = round(value, 2)
    
    return float(value)

def startActivityEngine(
    events: Dict[str, Event],
    stats: Dict[str, EventStats],
    numOfDays: int,
    logFilename: str
) -> None:
    print(f"[INFO] Starting activity engine for {numOfDays} days. Logs are written into: {logFilename}")
    with open(logFilename, "w") as f:
        f.write("Day:Event:Value\n")
        for day in range(1, numOfDays+1):
            print(f"[INFO] Generating events for day {day}/{numOfDays}:")
            for name, event in events.items():
                if name not in stats:
                    continue
                stat = stats[name]
                value = valueGenerator(event, stat)
                f.write(f"{day}:{name}:{value}\n")
    print(f"[INFO] Activity engine finished. Logs have been written into: {logFilename}")

# Analysis engine
def readTotalLogs(logFilename: str) -> Dict[str, List[Tuple[int, float]]]:
    data: Dict[str, List[Tuple[int, float]]] = {}
    with open(logFilename, "r") as f:
        header = f.readline()
        for line in f: 
            line = line.strip()
            if not line:
                continue
            dayStr, name, valueStr = line.split(":", 2)
            day = int(dayStr)
            value = float(valueStr)
            data.setdefault(name, []).append((day,value))
    return data

def startAnalysisEngine(
    logFilename: str,
    totalFilename: str,
    statsOutputFilename: str
) -> Dict[str, EventStats]:
    print(f"[INFO] Starting analysis engine for {logFilename}")
    data = readTotalLogs(logFilename)

    with open(totalFilename, "w") as tf:
        tf.write("event:day:total\n")
        for name, dayVal in data.items():
            for day, total in sorted(dayVal, key=lambda x: x[0]):
                tf.write(f"{name}:{day}:{total}\n")

    stats: Dict[str, EventStats] = {}
    with open(statsOutputFilename, "w") as f:
        f.write("event,mean,StandardDeviation\n")
        for name, dayVal in data.items():
            values = [v for _, v in dayVal]
            n = len(values)
            if n == 0:
                continue
            mean = sum(values)/n
            variance = sum((v - mean) ** 2 for v in values) / n
            stdDev = math.sqrt(variance)
            stats[name] = EventStats(name=name, mean=mean, stdDev=stdDev)
            f.write(f"{name}:{mean:.4f}:{stdDev:.4f}\n")
            print(f"[INFO] Baseline stats for {name}: mean={mean:.4f}, StandardDeviation={stdDev:.4f} (n={n})")
    
    print(f"[INFO] Analysis completed.\nDaily totals has been written to -> {totalFilename}\nStats has been written to -> {statsOutputFilename}")
    return stats

# Alert engine
def computeThreshold(events: Dict[str, Event]) -> float:
    totalWeight = sum(event.weight for event in events.values())
    return 2.0 * totalWeight

def startAlertEngine(
    events: Dict[str, Event],
    baselineStats: Dict[str, EventStats]
) -> None:
    print("[INFO] Starting alert engine")
    threshold = computeThreshold(events)
    print(f"[INFO] Threshold for this system is {threshold:.2f}")

    while True:
        print()
        print("---- Alert Engine Menu ----")
        print("1) Run anomaly detection with a new stats file.")
        print("2) Quit")

        userInput = input("Enter choice (1 or 2): ").strip()
        if userInput == "2":
            print("[INFO] Stopping alert engine")
            break
        if userInput != "1":
            print("Invalid choice, please enter 1 or 2")
            continue

        statsFilePath = input("Enter path for new stats file: ").strip()
        daysStr = input("Enter number of days to simulate for this run: ").strip()

        try:
            days = int(daysStr)
            if days <= 0:
                print("Days must be greater than 0.")
                continue
        except ValueError:
            print("Invalid number of days")
            continue

        try:
            newStats = readStats(statsFilePath)
        except Exception as e:
            print(f"[ERROR] Cannot read stats file: {e}")
            continue

        check(events, newStats)

        startActivityEngine(events, newStats, days, "live_log.txt")
        liveStats = startAnalysisEngine("live_log.txt", "live_totals.txt", "live_stats.txt")
        liveData = readTotalLogs("live_log.txt")

        allDaysStats = sorted({d for vals in liveData.values() for d,_ in vals})

        for day in allDaysStats:
            counter = 0
            for name, event in events.items():
                entries = [v for d, v in liveData[name] if d==day]
                if not entries:
                    continue
                val = entries[0]
                base = baselineStats[name]
                if base.stdDev > 0:
                    deviation = abs((val - base.mean) / base.stdDev)
                    counter += deviation * event.weight
            
                status = "FLAGGED" if counter >= threshold else "OK"
                print(f"[Day {day}]: Event name: [{event.name}] counter={counter:.2f} -> {status}")

# Main
def main(argv: List[str]) -> None:
    if len(argv) != 4: 
        print("Usage: python ids.py Events.txt Stats.txt Days")
        sys.exit(1)
    
    eventsPath = argv[1]
    statsPath = argv[2]
    days = int(argv[3])

    events = readEvents(eventsPath)
    stats = readStats(statsPath)

    check(events, stats)

    startActivityEngine(events, stats, days, "baseline_log.txt")

    baselineStats = startAnalysisEngine(
        "baseline_log.txt",
        "baseline_totals.txt",
        "baseline_stats.txt"
    )

    startAlertEngine(events, baselineStats)

if __name__ == "__main__":
    main(sys.argv)