from datetime import datetime


class TimeTools:
    @staticmethod
    def get_now_in_milliseconds():
        """
        Get the current time in milliseconds since the epoch.
        """
        return int(datetime.now().timestamp() * 1000)
