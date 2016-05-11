import codecs
import getpass
import datetime

class file_with_pos(object):
    def __init__(self, fp):
        self.fp = fp
        self.pos = 0
    def read(self, *args):
        data = self.fp.read(*args)
        self.pos += len(data)
        return data
    def tell(self):
        return self.pos


def read_lines_offsets(file_name):
    fp = codecs.open(file_name, 'r', encoding='ISO-8859-1')
    lines =[]
    line_offsets=[0]
    while True:
        line = fp.readline()
        if not line:
            break
        line_offsets.append(line_offsets[-1] + len(line))
        line = line.rstrip('\n')
        lines.append(line)
    return lines, line_offsets


def get_user_date_time_str():
    # add user name and date_time
    user_name = getpass.getuser()
    start_date_time = datetime.datetime.now()
    start_dt_str = '{user}_{year}_{month}_{day}_{hour}_{min}'.format(
        user = user_name,
        year = start_date_time.year,
        month = start_date_time.month,
        day = start_date_time.day,
        hour = start_date_time.hour,
        min = start_date_time.minute
    )
    return start_dt_str