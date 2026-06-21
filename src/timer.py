import threading
import time
from typing import Any, Callable, Union


class RepeatedTimer:
    def __init__(self, interval: Union[int, float], function: Callable, *args: Any, **kwargs: Any) -> None:
        """
        A repeated timer that executes a function after a fixed time and does not drift.

        Parameters
        ----------
        interval : Union[int, float]
              Execution interval in seconds.
          function : Callable
              Function to be executed periodically.
        """
        self._timer: threading.Timer | None = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.next_call = time.time()
        self.start()

    def _run(self) -> None:
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self) -> None:
        """
        Start the timer and run periodically.
        """
        if not self.is_running:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
            self._timer.start()
            self.is_running = True

    def stop(self) -> None:
        """
        Stop the timer and do not execute further iterations.
        """
        self._timer.cancel()  # type: ignore[union-attr]
        self.is_running = False
