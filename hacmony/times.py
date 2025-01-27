import datetime


class Times(object):
    def __init__(self):
        self.current_time = datetime.datetime.now()

    def time_diff(self, other):
        diff = other.current_time - self.current_time
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return diff.days, hours, minutes, seconds

    def time_out(self, other):
        days, hours, minutes, seconds = self.time_diff(other)
        # todo 根据timeout修改 目前先固定30mins
        if days > 0:
            print(f'start time: {self.current_time}')
            print(f'end time: {other.current_time}')
            return True
        if hours > 0:
            print(f'start time: {self.current_time}')
            print(f'end time: {other.current_time}')
            return True
        if minutes > 30:
            print(f'start time: {self.current_time}')
            print(f'end time: {other.current_time}')
            return True
        return False
