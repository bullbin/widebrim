from time import sleep, perf_counter

class AltClock():

    PYGAME_GET_FPS_AVERAGE_CALLS    = 10
    PLATFORM_CLOCK_PRECISION_SEC    = 0.0015     # 1.5ms found best on Windows 10. YMMV

    def __init__(self):
        self.prevFrame = perf_counter()
        self.frameTimeHistory = []

    def tick(self, gameClockInterval):
        self.frameTimeHistory.append(self.tickAltTimerHybrid(gameClockInterval))
        if len(self.frameTimeHistory) > AltClock.PYGAME_GET_FPS_AVERAGE_CALLS:
            self.frameTimeHistory = self.frameTimeHistory[-AltClock.PYGAME_GET_FPS_AVERAGE_CALLS:]
        return self.frameTimeHistory[-1]

    def tickAltTimerHybrid(self, gameClockInterval):
        lastPrevFrame = self.prevFrame
        timeIdle = gameClockInterval - (perf_counter() - lastPrevFrame)
        timeSleep = timeIdle - AltClock.PLATFORM_CLOCK_PRECISION_SEC    # More stable frametimes if inaccuracy subtracted rather than sleep period calculated
        if timeSleep > 0:           # Sleep some multiple of known-good precision
            sleep(timeSleep)
        while (perf_counter() - lastPrevFrame) < gameClockInterval: # Busy-wait remaining frame time
            pass
        self.prevFrame = perf_counter()
        return (perf_counter() - lastPrevFrame) * 1000

    def get_fps(self):
        if len(self.frameTimeHistory) == AltClock.PYGAME_GET_FPS_AVERAGE_CALLS:
            total = 0
            for frameTime in self.frameTimeHistory:
                total += frameTime
            return 1000 / (total / AltClock.PYGAME_GET_FPS_AVERAGE_CALLS)
        return 0