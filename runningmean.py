import statistics

class RunningMean:
    def __init__(self, width):
        self.width = width
        self.mes = []
        self.des = []
        self.total = 0
        self.qvar = 0
        self.var = 0

    def mean(self, val):
        self.total += val
        self.mes.append(val)

        qdev = (val - (self.total / len(self.mes))) ** 2
        self.qvar += qdev
        self.des.append(qdev)

        if len(self.mes) > self.width:
            self.total -= self.mes.pop(0)
            self.qvar -= self.des.pop(0)

        self.var = (self.qvar / len(self.mes)) ** 0.5
        return self.total / len(self.mes)

class AdaptiveRunningMean:


    def __init__(self, minwidth=8, maxwidth=64, fup=0.0, fdown = 0.0):
        self.MinWidth = minwidth
        self.MaxWidth = maxwidth
        self.Width = 1
        self.FUp = fup
        self.FDown = fdown
        self.Stack = []
        self.des = []
        self.total = 0
        self.qvar = 0
        self.var = 0
        self.OldSgn = None
        self.NewSgn = None

    def sign(self, x):
        return x and (1, -1)[x < 0]

    def do(self, val, func = statistics.mean):
        self.Stack.append(val)
        if len(self.Stack) > 2:

            if self.sign(self.Stack[-1]-self.Stack[-2]) == self.sign(self.Stack[-2]-self.Stack[-3]):
                self.Width -= self.FDown
            else:
                self.Width += self.FUp

        self.Width = max(self.Width, self.MinWidth)
        self.Width = min(self.Width, self.MaxWidth, len(self.Stack))

        if len(self.Stack) > self.Width + 1:
            self.Stack.pop(0)

        # print("Len ", len(self.Stack), "Width ", self.Width, "Data ", self.Stack[-(round(self.Width)):])
        return func(self.Stack[-(round(self.Width)):])

    def reset(self):
        self.Stack = []
        self.Width = self.MinWidth



if __name__ == '__main__':

    M = AdaptiveRunningMean(minwidth=3, maxwidth=8, fup=0.7, fdown=0.3)

    val = input("?: ")
    while val is not None:
        print(M.do(float(val), statistics.median))
        val = input("?: ")










    def mean(self, val):
        return
