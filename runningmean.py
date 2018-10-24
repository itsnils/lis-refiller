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