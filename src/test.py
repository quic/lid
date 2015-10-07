
class a:
    def __init__(self):
        self.self_str = "self string"

    def fun1(self):
        str_mod = "original"
        d1 = {'hi':1, 'hello':2}

        print ('str_mod = {}'.format(id(str_mod)))
        print ('d1 = {}'.format(id(d1)))

        self.fun2(str_mod, d1)

        print(str_mod)
        print ('str_mod = {}'.format(id(str_mod)))
        print ('d1 = {}'.format(id(d1)))
        
        
    def fun2(self, inputStr, td):
        print ('inputStr = {}'.format(id(inputStr)))
        inputStr = "modified"
        print ('inputStr = {}'.format(id(inputStr)))
        print ('td = {}'.format(id(td)))
        td['bonjour'] = 3
        print ('td = {}'.format(id(td)))

ta = a()
ta.fun1()
