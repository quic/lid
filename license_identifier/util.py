
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
    fp = open(file_name, 'r', encoding='ISO-8859-1')
    lines =[]
    line_offsets=[]
    while True:
        line_offsets.append(fp.tell())
        line = fp.readline()
        if not line:
            break
        line = line.rstrip('\n')
        lines.append(line)
    return lines, line_offsets


